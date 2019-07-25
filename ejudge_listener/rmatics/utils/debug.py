import os
import time
from math import floor


def build_protocol_dump_filename(run_id: int,
                                 protocol_dir: str) -> str:
    """Build absolute path for debug protocol dump

    :param run_id: corresponding run ID
    :param protocol_dir: absolute path for protocol directory
    :return: absolute path for current protocol dump
    """
    timestamp = floor(time.time())

    filename = '{0}/{1}_{2}.xml'.format(
        protocol_dir,
        run_id,
        timestamp,
    )
    filename = os.path.normpath(filename)

    return filename


def dump_xml_protocol(xml_content: str, run_id: int,
                      protocol_dir: str) -> None:
    """Save provided XML protocol string to debug directory

    :param xml_content: String with XML protocol to dump
    :param run_id: corresponding run ID
    :param protocol_dir: absolute path for protocol directory
    :return:
    """
    try:
        filename = build_protocol_dump_filename(run_id, protocol_dir)

        with open(filename, 'w') as protocol_file:
            protocol_file.write(xml_content)
    except Exception as exc:
        # DEBUG: we silently swallow all errors not to break
        # flow while dumping protocol to filesystem
        pass
