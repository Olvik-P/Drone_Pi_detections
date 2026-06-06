from app_msp.osd_msp_client import msp_client

if __name__ == '__main__':
    import platform

    # Автоопределение порта в зависимости от ОС
    if platform.system() == 'Windows':
        port = 'COM4'
    else:
        port = '/dev/ttyS0'

    msp_client.show_string_dji_googles(port, 0, 0, text='Test MSP')
