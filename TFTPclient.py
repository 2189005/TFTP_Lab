import socket
import argparse
from struct import pack

#기본 설정 값들
DEFAULT_PORT = 69
BLOCK_SIZE = 512
DEFAULT_TRANSFER_MODE = 'octet'
TIMEOUT = 5  # 타임아웃 시간 (초)

#TFTP의 메시지 타입
OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
#전송 모드
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}

#TFTP 에러코드 및 설명
ERROR_CODE = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}

#RRQ 메시지를 서버에 전송
def send_rrq(filename, mode):
    # RRQ 메시지의 포맷을 설정하고 서버에 전송
    format_str = f'>h{len(filename)}sB{len(mode)}sB'
    rrq_message = pack(format_str, OPCODE['RRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(rrq_message, server_address)
    print(rrq_message)

# ACK 메시지를 서버에 전송
def send_ack(seq_num, server):
    # ACK 메시지의 포맷을 설정하고 서버에 전송
    format_str = f'>hh'
    ack_message = pack(format_str, OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print(seq_num)
    print(ack_message)


# 명령행 인수 파싱
parser = argparse.ArgumentParser(description='TFTP 클라이언트 프로그램')
parser.add_argument(dest="host", help="서버 IP 주소", type=str)
parser.add_argument(dest="operation", help="파일을 받거나 보냄 (get 또는 put)", type=str)
parser.add_argument(dest="filename", help="전송할 파일의 이름", type=str)
parser.add_argument("-p", "--port", dest="port", type=int)
args = parser.parse_args()

# UDP 소켓 생성 및 타임아웃 설정
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 9000))

# 서버 IP 및 포트 설정
server_ip = args.host
server_port = args.port or DEFAULT_PORT
server_address = (server_ip, server_port)

#전송 모드, 동작, 파일 이름 설정
mode = DEFAULT_TRANSFER_MODE
operation = args.operation
filename = args.filename

# RRQ 메시지 전송
send_rrq(args.filename, DEFAULT_TRANSFER_MODE)

# 서버로부터 전송된 데이터를 저장할 파일 열기
file = open(args.filename, 'wb')
expected_block_number = 1

while True:
    try:
        # 서버로부터 데이터 수신
        data, server_new_socket = sock.recvfrom(516)
        opcode = int.from_bytes(data[:2], 'big')

        # 메시지 타입 확인
        if opcode == OPCODE['DATA']:
            block_number = int.from_bytes(data[2:4], 'big')
            # 중복된 블록 번호를 피하기 위해 ACK를 보내기 전에 블록 번호를 확인
            if block_number == expected_block_number:
                send_ack(block_number, server_new_socket)
                file_block = data[4:]
                file.write(file_block)
                expected_block_number = expected_block_number + 1
                print(file_block.decode())
            else:
                # 수신된 블록 번호가 기대하는 블록 번호와 일치하지 않으면,
                # 마지막으로 성공적으로 수신한 블록에 대한 ACK를 재전송
                send_ack(expected_block_number - 1, server_new_socket)
        #에러코드 확인
        elif opcode == OPCODE['ERROR']:
            error_code = int.from_bytes(data[2:4], byteorder='big')
            print(ERROR_CODE[error_code])
            break

        else:
            break

        # 타임아웃 조건을 확인하고 루프를 종료
        if len(file_block) < BLOCK_SIZE:
            file.close()
            print(len(file_block))
            break

    except socket.timeout:
        #소켓 수신 시 타임아웃 발생한 경우 예외 처리
        print("타임아웃")

        #파일을 닫고 루프를 종료
        file.close()
        break
