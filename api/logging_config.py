import logging
from pathlib import Path

Path('logs').mkdir(exist_ok=True)

def get_logger(name, logfile):
    logger=logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh=logging.FileHandler(Path('logs')/logfile, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    logger.addHandler(fh)
    logger.propagate=False
    return logger
