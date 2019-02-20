import os

from ejudge_listener.models import db
from ejudge_listener.protocol.run import read_file_unknown_encoding
from ejudge_listener.rmatics.ejudge.serve_internal import EjudgeContestCfg
from ejudge_listener.rmatics.utils.json_type import JsonType


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
    contest_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=False)
    ejudge_contest_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=False)
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
        if self.get_test_size(int(test_num)) <= 255:
            test["input"] = self.get_test(int(test_num), size=size)
            test["big_input"] = False
        else:
            test["input"] = self.get_test(int(test_num), size=size) + "...\n"
            test["big_input"] = True

        if self.get_corr_size(int(test_num)) <= 255:
            test["corr"] = self.get_corr(int(test_num), size=size)
            test["big_corr"] = False
        else:
            test["corr"] = self.get_corr(int(test_num), size=size) + "...\n"
            test["big_corr"] = True
        return test

    def get_corr_size(self, test_num):
        conf = EjudgeContestCfg(number=self.ejudge_contest_id)
        prob = conf.getProblem(self.problem_id)

        corr_file_name = (prob.tests_dir + prob.corr_pat) % int(test_num)
        return os.stat(corr_file_name).st_size

