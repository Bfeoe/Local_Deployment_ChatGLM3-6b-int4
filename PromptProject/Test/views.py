import os
import subprocess
import os
from django.shortcuts import render


def main_view(request):
    # 获取请求中的选择模型和语言
    model = request.GET.get('model', 'qwen')
    language = request.GET.get('language', 'zh')
    
    script_path = '/home/bfeoe/NLP/main.py'
    process = subprocess.Popen(['python', script_path, '--model', model, '--language', language],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 读取文件内容
    filename = f"{model}_result_{language}.txt"
    file_path = os.path.join('/home/bfeoe/NLP/result/', filename)
    print(file_path)

    # 检查文件是否存在
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
    else:
        file_content = f"文件 {filename} 不存在"
    

    # 渲染页面
    return render(request, 'main.html', {
        'model': model,
        'language': language,
        'file_content': file_content
    })