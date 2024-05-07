from http import HTTPStatus
import argparse
import re
import logging
import json
from os.path import basename
import requests
import os


# 设置根目录
root_path = "/home/bfeoe/NLP/"

# 全局常规设置: 缓存文件，错误文件，存取正读到的行的文件
log_file_path = root_path + "result/log/app.log"
error_file_path = root_path + "data/error_data.txt"
lines_file_path = root_path + "result/log/last_line.json"

# 两个正则表达式，用于匹配json格式
regex_one = r'\{.*?\}'
regex_two = r'\{(.*?)\}'

# Config类的定义，以便调用
class Config:
    def __init__(self, model=None, language=None, data_path=None):
        self.model = model
        self.language = language
        self.data_path = data_path
        self.result_file_path = None
        self.prompt_file_path = None
        self.prompt = None

    # 更新文件路径
    def update_file_path(self):
        self.result_file_path = f"{root_path}result/{self.model}_result_{self.language}.txt"
        self.prompt_file_path = f'{root_path}data/prompt/prompt_{self.language}.txt'

    # 更新prompt
    def update_prompt(self):
        try:
            with open(self.prompt_file_path, 'r', encoding='utf-8') as prompt_file:
                self.prompt = prompt_file.read().strip()
        except Exception as e:
            logging.error(f"Error open file{self.prompt_file_path}: {str(e)}")
            print(f"Error open file{self.prompt_file_path}: {str(e)}")


# 全局argparse设置
def parse_arguments(config):
    parser = argparse.ArgumentParser(description="通过命令行参数选择模型及prompt语言")
    # 添加模型的参数
    parser.add_argument("--model", choices=["qwen", "glm"], default="qwen", nargs="?",
                        help="选择要使用的模型：qwen 或 glm")
    parser.add_argument("--language", choices=["zh", "en"], default="zh", nargs="?",
                        help="选择prompt语言：zh 或 en")
    parser.add_argument("--data_path", type=str , default="data/data.txt", nargs="?",
                        help="填写文件路径")
    args = parser.parse_args()
    config.model = args.model
    config.language = args.language
    config.data_path = root_path + args.data_path
    return config


# 设置日志记录器
if not os.path.exists(log_file_path):
    with open(log_file_path, 'w') as file:
        pass
logging.basicConfig(filename=log_file_path, level=logging.INFO)


# 加载上次处理到的行数
def load_last_processed_line(file_path: str):
    if os.path.isfile(lines_file_path):
        file_name = basename(file_path)

        with open(lines_file_path, 'r') as progress_file:
            try:
                json_data = json.load(progress_file)
                if file_name in json_data:
                    # 返回对应的行号
                    return int(json_data[file_name])
                
            # 没有对应的文件也返回0
            except json.JSONDecodeError:
                return 0
    return 0


# 保存当前已处理到的行数
def save_last_processed_line(line_number: int, file_path: str):
    file_name = basename(file_path)
    with open(lines_file_path, 'r+') as progress_file:
        # 若文件为空则初始化为空字典
        try:
            json_data = json.load(progress_file)
        except json.JSONDecodeError:
            json_data = {}

        # 更新行号
        json_data[file_name] = line_number

        # 清空文件内容
        progress_file.seek(0)
        progress_file.truncate()

        # 将更新的数据写回文件
        json.dump(json_data, progress_file, ensure_ascii=False, indent=4)


# 回答问题的函数
def response(config: Config, content: str):
    data = json.dumps({"prompt": config.prompt+content})
    data = data.encode("utf-8")
    url = "http://localhost:8848/" + config.model
    headers = {"Content-Type": "application/json"}
    api_response = requests.get(url, headers=headers, stream=True, data=data)
    if api_response.status_code == HTTPStatus.OK:
        print("预测结果：", api_response.text.replace("\\", ""))
        return api_response.text.replace("\\", "")
    else:
        print(f"请求失败，状态码：{api_response.status_code}")
        logging.error(f'请求失败，状态码：{api_response.status_code}')


# 数据预处理
def data_pre(config: Config):
    # 加载上次处理到的行数和文件地址
    last_line = load_last_processed_line(lines_file_path)

    # 打开输入文件
    try:
        with open(config.data_path, 'r', encoding='utf-8') as data_file:
            lines = data_file.readlines()[last_line:]
    except Exception as e:
        logging.error(f"Error open file:'{config.data_path}': {str(e)}")
        print(f"Error open file:'{config.data_path}': {str(e)}")
    return lines, last_line


# 抽取三元组
def extraction_triplet(config: Config, data_lines: list, last_line_number: int, name: str):
    try:
        for line_index, line in enumerate(data_lines, start=last_line_number+1):
            answer = response(config, line.strip())

            # 做正则匹配
            matches = re.findall(regex_one, answer, re.DOTALL)
            mat = re.findall(regex_two, answer)

            if not matches and not mat:
                # 如果没有找到匹配项，写入到error_data.txt文件
                with open(error_file_path, "a", encoding='utf-8') as error_file:
                    error_file.write(f'{line}')

            logging.info(f"Line {line_index}: {matches}")
            with open(config.result_file_path, 'a', encoding='utf-8') as result_file:
                for item in matches:
                    result_file.write(f'{item}\n')
                result_file.write('\n')
            if name != "error_data":
                save_last_processed_line(line_index, config.data_path)

        logging.info(f'抽取三元组已全部写入{config.result_file_path}中')
        print(f'抽取三元组已经全部写入{config.result_file_path}中')
    except Exception as e:
        logging.error(f"Error write: {str(e)}")
        print(f"Error write: {str(e)}")
        with open(error_file_path, "a", encoding='utf-8') as error_file:
            error_file.write(f'{line}\n')


# 主函数
def main():
    # 初始化配置
    config = Config()
    config = parse_arguments(config)
    config.update_file_path()
    config.update_prompt()

    logging.info(f'正在使用{config.model}模型，使用{config.language}prompt，处理名为《{basename(config.data_path)}》文件')
    print(f'正在使用{config.model}模型，使用{config.language}prompt，处理名为《{basename(config.data_path)}》文件')

    lines, last_line = data_pre(config)

    extraction_triplet(config, lines, last_line, config.data_path)

    # 写入空字符串会清空文件内容
    with open(error_file_path,'r', encoding='utf-8') as f:
        error_lines = f.readlines()
    with open(error_file_path, 'w', encoding='utf-8') as f:
        f.write('')

    if len(error_lines) > 0:
        print('存在部分处理异常语句，正在重新处理')
        logging.info('存在部分处理异常语句，正在重新处理')
        extraction_triplet(config, error_lines, 0, "error_data")

    # 重新处理后再检查一次
    with open(error_file_path,'r', encoding='utf-8') as f:
        error_lines = f.readlines()
        if len(error_lines) > 0:
            print(f'仍存在异常语句，详情请查看{error_file_path}文件')
            logging.info(f'仍存在异常语句，详情请查看{error_file_path}文件')


if __name__ == '__main__':
    main()
