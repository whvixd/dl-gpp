import time
import logging
import logging.handlers


def wrapperLogging():
    debug_format = '%(asctime)s-[%(filename)s-->line:%(lineno)d]-%(levelname)s:%(message)s'
    console_handler = logging.StreamHandler()

    # 按天记录日志
    file_run_log = logging.handlers.TimedRotatingFileHandler(
        "../log/debug_" + time.strftime("%Y%m%d", time.localtime()) + ".log", backupCount=0,
        encoding='utf-8',
        when='D', interval=1)

    # file_handler = logging.FileHandler("./debug.log", mode="a", encoding="utf-8")
    logging.basicConfig(level=logging.DEBUG,  # 设置级别，根据等级显示
                        format=debug_format,  # 设置输出格式
                        handlers=[console_handler, file_run_log])

    return logging
