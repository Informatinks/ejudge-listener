import os
import xml
import xml.dom.minidom
import zipfile

from flask import current_app

from ejudge_listener.extensions import db
from ejudge_listener.protocol.ejudge_archive import EjudgeArchiveReader
from ejudge_listener.protocol.exceptions import AuditNotFoundError, TestsNotFoundError
from ejudge_listener.protocol.run import (
    safe_open,
    submit_path,
    to32,
    get_string_status,
    get_protocol_from_file,
    read_file_unknown_encoding
)

from .rmatics.ejudge.serve_internal import EjudgeContestCfg
from .rmatics.utils.json_type import JsonType


class Problem(db.Model):
    __table_args__ = {'schema': 'moodle'}
    __tablename__ = 'mdl_problems'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255))
    content = db.Column(db.Text)
    review = db.Column(db.Text)
    hidden = db.Column(db.Boolean)
    timelimit = db.Column(db.Float)
    memorylimit = db.Column(db.Integer)
    description = db.Column(db.Text)
    analysis = db.Column(db.Text)
    sample_tests = db.Column(db.Unicode(255))
    sample_tests_html = db.Column(db.Text)
    sample_tests_json = db.Column(JsonType)
    show_limits = db.Column(db.Boolean)
    output_only = db.Column(db.Boolean)
    pr_id = db.Column(db.Integer, db.ForeignKey('moodle.mdl_ejudge_problem.id'))

    def __init__(self, *args, **kwargs):
        super(Problem, self).__init__(*args, **kwargs)
        self.hidden = 1
        self.show_limits = True


class EjudgeProblem(Problem):
    """
    Модель задачи из ejudge

    ejudge_prid -- primary key, на который ссылается Problem.pr_id.
        После инициализации, соответствтующему объекту Problem проставляется корректный pr_id

    contest_id --

    ejudge_contest_id -- соответствует contest_id из ejudge

    secondary_ejudge_contest_id --

    problem_id -- соответствует problem_id из ejudge

    short_id -- короткий id (обычно буква)
    """

    __table_args__ = (
        db.Index('ejudge_contest_id_problem_id', 'ejudge_contest_id', 'problem_id'),
        {'schema': 'moodle', 'extend_existing': True}
    )
    __tablename__ = 'mdl_ejudge_problem'
    __mapper_args__ = {'polymorphic_identity': 'ejudgeproblem'}

    ejudge_prid = db.Column('id', db.Integer, primary_key=True)  # global id in ejudge
    contest_id = db.Column(db.Integer, primary_key=True, nullable=False,
                           autoincrement=False)
    ejudge_contest_id = db.Column(db.Integer, primary_key=True, nullable=False,
                                  autoincrement=False)
    secondary_ejudge_contest_id = db.Column(db.Integer, nullable=True)
    problem_id = db.Column(db.Integer, primary_key=True, nullable=False,
                           autoincrement=False)  # id in contest
    short_id = db.Column(db.Unicode(50))
    ejudge_name = db.Column('name', db.Unicode(255))

    @staticmethod
    def create(**kwargs):
        """
        При создании EjudgeProblem сначала в базу пишет Problem потом EjudgeProblem,
        из-за чего pr_id не проставляется
        """
        instance = EjudgeProblem(**kwargs)
        db.session.add(instance)
        db.session.flush([instance])

        problem_id = instance.id
        ejudge_problem_id = instance.pr_id
        db.session.commit()

        problem_instance = db.session.query(Problem).filter_by(id=problem_id).one()
        problem_instance.pr_id = ejudge_problem_id
        db.session.commit()

        return db.session.query(EjudgeProblem).filter_by(id=problem_id).one()

    def get_test(self, test_num, size=255):
        conf = EjudgeContestCfg(number=self.ejudge_contest_id)
        prob = conf.getProblem(self.problem_id)

        test_file_name = (prob.tests_dir + prob.test_pat) % int(test_num)
        if os.path.exists(test_file_name):
            res = read_file_unknown_encoding(test_file_name, size)
        else:
            res = test_file_name
        return res

    def get_test_size(self, test_num):
        conf = EjudgeContestCfg(number=self.ejudge_contest_id)
        prob = conf.getProblem(self.problem_id)

        test_file_name = (prob.tests_dir + prob.test_pat) % int(test_num)
        return os.stat(test_file_name).st_size

    def get_corr(self, test_num, size=255):
        conf = EjudgeContestCfg(number=self.ejudge_contest_id)
        prob = conf.getProblem(self.problem_id)

        corr_file_name = (prob.tests_dir + prob.corr_pat) % int(test_num)
        if os.path.exists(corr_file_name):
            res = read_file_unknown_encoding(corr_file_name, size)
        else:
            res = corr_file_name
        return res

    def get_test_full(self, test_num, size=255):
        """
        Возвращает словарь с полной информацией о тесте
        """
        test = {}
        try:
            if self.get_test_size(int(test_num)) <= 255:
                test["input"] = self.get_test(int(test_num), size=size)
                test["big_input"] = False
            else:
                test["input"] = self.get_test(int(test_num), size=size) + "...\n"
                test["big_input"] = True
        except:
            test["input"] = ''
            test["big_input"] = False

        try:
            if self.get_corr_size(int(test_num)) <= 255:
                test["corr"] = self.get_corr(int(test_num), size=size)
                test["big_corr"] = False
            else:
                test["corr"] = self.get_corr(int(test_num), size=size) + "...\n"
                test["big_corr"] = True
        except:
            test["corr"] = ''
            test["big_corr"] = False

        return test

    def get_corr_size(self, test_num):
        conf = EjudgeContestCfg(number=self.ejudge_contest_id)
        prob = conf.getProblem(self.problem_id)

        corr_file_name = (prob.tests_dir + prob.corr_pat) % int(test_num)
        return os.stat(corr_file_name).st_size


def lazy(func):
    """
    A decorator function designed to wrap attributes that need to be
    generated, but will not change. This is useful if the attribute is
    used a lot, but also often never used, as it gives us speed in both
    situations.
    """

    def cached(self, *args):
        name = "_" + func.__name__
        try:
            return getattr(self, name)
        except AttributeError:
            value = func(self, *args)
            setattr(self, name, value)
            return value

    return cached


class EjudgeRun(db.Model):
    __table_args__ = (db.ForeignKeyConstraint(
        ['contest_id', 'prob_id'],
        ['moodle.mdl_ejudge_problem.ejudge_contest_id',
         'moodle.mdl_ejudge_problem.problem_id']
    ), {'schema': 'ejudge'})
    __tablename__ = 'runs'

    run_id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    create_nsec = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    prob_id = db.Column(db.Integer)  # TODO: rename to problem_id
    lang_id = db.Column(db.Integer)
    status = db.Column(db.Integer)
    ssl_flag = db.Column(db.Integer)
    ip_version = db.Column(db.Integer)
    ip = db.Column(db.String(64))
    hash = db.Column(db.String(128))
    run_uuid = db.Column(db.String(40))
    score = db.Column(db.Integer)
    test_num = db.Column(db.Integer)
    score_adj = db.Column(db.Integer)
    locale_id = db.Column(db.Integer)
    judge_id = db.Column(db.Integer)
    variant = db.Column(db.Integer)
    pages = db.Column(db.Integer)
    is_imported = db.Column(db.Integer)
    is_hidden = db.Column(db.Integer)
    is_readonly = db.Column(db.Integer)
    is_examinable = db.Column(db.Integer)
    mime_type = db.Column(db.String(64))
    examiners0 = db.Column(db.Integer)
    examiners1 = db.Column(db.Integer)
    examiners2 = db.Column(db.Integer)
    exam_score0 = db.Column(db.Integer)
    exam_score1 = db.Column(db.Integer)
    exam_score2 = db.Column(db.Integer)
    last_change_time = db.Column(db.DateTime)
    last_change_nsec = db.Column(db.Integer)
    is_marked = db.Column(db.Integer)
    is_saved = db.Column(db.Integer)
    saved_status = db.Column(db.Integer)
    saved_score = db.Column(db.Integer)
    saved_test = db.Column(db.Integer)
    passed_mode = db.Column(db.Integer)
    eoln_type = db.Column(db.Integer)
    store_flags = db.Column(db.Integer)
    token_flags = db.Column(db.Integer)
    token_count = db.Column(db.Integer)

    problem = db.relationship(
        'EjudgeProblem',
        backref=db.backref('ejudge_runs', lazy='dynamic'),
        uselist=False,
    )

    SIGNAL_DESCRIPTION = {
        1: "Hangup detected on controlling terminal or death of controlling process",
        2: "Interrupt from keyboard",
        3: "Quit from keyboard",
        4: "Illegal Instruction",
        6: "Abort signal",
        7: "Bus error (bad memory access)",
        8: "Floating point exception",
        9: "Kill signal",
        11: "Invalid memory reference",
        13: "Broken pipe: write to pipe with no readers",
        14: "Timer signal",
        15: "Termination signal",
        25: 'File size limit exceeded',
    }

    @db.reconstructor
    def init_on_load(self):
        self.out_path = "/home/judges/{0:06d}/var/archive/output/{1}/{2}/{3}/{4:06d}.zip".format(
            self.contest_id,
            to32(self.run_id // (32 ** 3) % 32),
            to32(self.run_id // (32 ** 2) % 32),
            to32(self.run_id // 32 % 32),
            self.run_id,
        )
        self._out_arch = None
        self._out_arch_file_names = set()

    @lazy
    def get_audit(self):
        try:
            data = safe_open(submit_path(current_app.config['AUDIT_PATH'],
                                         self.contest_id, self.run_id), 'r').read()
        except FileNotFoundError:
            raise AuditNotFoundError  # TODO: исправить этот костыль, он относится к run.py:188
        if type(data) == bytes:
            data = data.decode('ascii')
        return data

    @lazy
    def get_sources(self):
        data = safe_open(submit_path(current_app.config['SOURCES_PATH'],
                                     self.contest_id, self.run_id), 'rb').read()
        for encoding in ['utf-8', 'ascii', 'windows-1251']:
            try:
                data = data.decode(encoding)
            except:
                print('decoded:', encoding)
                pass
            else:
                break
        else:
            return 'Ошибка кодировки'
        return data

    def get_output_file(
            self, test_num, tp="o", size=None
    ):  # tp: o - output, e - stderr, c - checker
        data = (
            self.get_output_archive().getfile(
                "{0:06}.{1}".format(test_num, tp)).decode('ascii'))
        if size is not None:
            data = data[:size]
        return data

    def get_output_file_size(
            self, test_num, tp="o"
    ):  # tp: o - output, e - stderr, c - checker
        data = (
            self.get_output_archive().getfile(
                "{0:06}.{1}".format(test_num, tp)).decode('ascii'))
        return len(data)

    def get_output_archive(self):
        if "output_archive" not in self.__dict__:
            self.output_archive = EjudgeArchiveReader(
                submit_path(current_app.config['OUTPUT_PATH'],
                            self.contest_id, self.run_id))
        return self.output_archive

    def get_test_full_protocol(self, test_num):
        """
        Возвращает полный протокол по номеру теста
        :param test_num: - str
        """
        judge_info = self.judge_tests_info[test_num]
        test_protocol = self.problem.get_test_full(test_num)

        test_protocol.update(self.tests[test_num])

        test_protocol['big_output'] = False
        try:
            if self.get_output_file_size(int(test_num), tp='o') <= 255:
                test_protocol['output'] = self.get_output_file(int(test_num),
                                                               tp='o')
            else:
                test_protocol['output'] = (
                        self.get_output_file(int(test_num), tp='o',
                                             size=255) + '...\n'
                )
                test_protocol['big_output'] = True
        except OSError as e:
            test_protocol['output'] = judge_info.get('output', '')

        try:
            if self.get_output_file_size(int(test_num), tp='c') <= 255:
                test_protocol['checker_output'] = self.get_output_file(
                    int(test_num), tp='c'
                )
            else:
                test_protocol['checker_output'] = (
                        self.get_output_file(int(test_num), tp='c',
                                             size=255) + '...\n'
                )
        except OSError as e:
            test_protocol['checker_output'] = judge_info.get('checker', '')

        try:
            if self.get_output_file_size(int(test_num), tp='e') <= 255:
                test_protocol['error_output'] = self.get_output_file(
                    int(test_num), tp='e'
                )
            else:
                test_protocol['error_output'] = (
                        self.get_output_file(int(test_num), tp='e',
                                             size=255) + '...\n'
                )
        except OSError as e:
            test_protocol['error_output'] = judge_info.get('stderr', '')

        if 'term-signal' in judge_info:
            test_protocol['extra'] = 'Signal %(signal)s. %(description)s' % {
                'signal': judge_info['term-signal'],
                'description': self.SIGNAL_DESCRIPTION.get(
                    judge_info['term-signal'], 'Undefined signal'),
            }
        if 'exit-code' in judge_info:
            test_protocol['extra'] = test_protocol.get(
                'extra', ''
            ) + '\n Exit code %(exit_code)s. ' % {
                                         'exit_code': judge_info['exit-code']}

        for type_ in [('o', 'output'), ('c', 'checker_output'),
                      ('e', 'error_output')]:
            file_name = '{0:06d}.{1}'.format(int(test_num), type_[0])
            if self._out_arch is None:
                try:
                    self._out_arch = zipfile.ZipFile(self.out_path, 'r')
                    self._out_arch_file_names = set(self._out_arch.namelist())
                except:
                    pass
            if file_name not in self._out_arch_file_names or type_[1] in test_protocol:
                continue
            with self._out_arch.open(file_name, 'r') as f:
                test_protocol[type_[1]] = f.read(1024).decode(
                    "utf-8") + "...\n"

        return test_protocol

    def parsetests(self):
        """
        Parse tests data from xml archive
        """
        self.test_count = 0
        self.tests = {}
        self.judge_tests_info = {}
        self.status_string = None
        self.compiler_output = None
        self.host = None
        self.maxtime = None

        if not self.xml:
            raise TestsNotFoundError

        rep = self.xml.getElementsByTagName('testing-report')[0]
        self.tests_count = int(rep.getAttribute('run-tests'))
        self.status_string = rep.getAttribute('status')

        compiler_output_elements = self.xml.getElementsByTagName(
            'compiler_output')
        if compiler_output_elements:
            self.compiler_output = getattr(
                compiler_output_elements[0].firstChild, 'nodeValue', ''
            )

        host_elements = self.xml.getElementsByTagName('host')
        if host_elements:
            self.host = host_elements[0].firstChild.nodeValue

        for node in self.xml.getElementsByTagName('test'):
            number = node.getAttribute('num')
            status = node.getAttribute('status')
            time = node.getAttribute('time')
            real_time = node.getAttribute('real-time')
            max_memory_used = node.getAttribute('max-memory-used')
            self.test_count += 1

            try:
                time = int(time)
            except ValueError:
                time = 0

            try:
                real_time = int(real_time)
            except ValueError:
                real_time = 0

            test = {
                'status': status,
                'string_status': get_string_status(status),
                'real_time': real_time,
                'time': time,
                'max_memory_used': max_memory_used,
            }
            judge_info = {}

            for _type in (
                    'input', 'output', 'correct', 'stderr', 'checker'):
                lst = node.getElementsByTagName(_type)
                if lst and lst[0].firstChild:
                    judge_info[_type] = lst[0].firstChild.nodeValue
                else:
                    judge_info[_type] = ''

            if node.hasAttribute('term-signal'):
                judge_info['term-signal'] = int(
                    node.getAttribute('term-signal'))
            if node.hasAttribute('exit-code'):
                judge_info['exit-code'] = int(
                    node.getAttribute('exit-code'))

            self.judge_tests_info[number] = judge_info
            self.tests[number] = test
        try:
            # print([test['time'] for test in self.tests.values()] +
            # [test['real_time'] for test in self.tests.values()])
            self.maxtime = max(
                [test['time'] for test in self.tests.values()]
                + [test['real_time'] for test in self.tests.values()]
            )
        except ValueError:
            pass

        # If we have 0 tests, Ejudge has not yet completed
        # writing tests to filesystem. Raise error to retry retrieve.
        # Avoids possible race contidion case.
        if len(tests) == 0:
            raise TestsNotFoundError

    @lazy
    def _get_protocol(self):
        filename = submit_path(current_app.config['PROTOCOLS_PATH'],
                               self.contest_id, self.run_id)
        if filename:
            return get_protocol_from_file(filename)
        else:
            return '<a></a>'

    protocol = property(_get_protocol)

    @lazy
    def fetch_tested_protocol_data(self):
        try:
            self.xml = xml.dom.minidom.parseString(str(self.protocol))
            self.parsetests()
        except xml.parsers.expat.ExpatError as exc:
            # If there are parse errors
            raise TestsNotFoundError
