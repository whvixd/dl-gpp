
def wrapper(logging):
    debug_format = '%(asctime)s-[%(filename)s-->line:%(lineno)d]-%(levelname)s:%(message)s'
    console_handler = logging.StreamHandler()

    file_handler = logging.FileHandler("./debug.log", mode="a", encoding="utf-8")

    logging.basicConfig(level=logging.DEBUG,  # 设置级别，根据等级显示
                        format=debug_format,  # 设置输出格式
                        handlers=[console_handler, file_handler])