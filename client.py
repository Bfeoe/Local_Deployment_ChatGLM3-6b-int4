import random
import dashscope
from dashscope import Generation
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from transformers import AutoTokenizer, AutoModel
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

model_path = "chatglm_6b_int4_model"
dashscope.api_key = ""


tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModel.from_pretrained(model_path, trust_remote_code=True).half().quantize(4).cuda()


# 请求处理函数
async def predict_qwen(request):
    query_params = await request.json()
    prompt = query_params["prompt"]
    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}]
    response = Generation.call("qwen-turbo",
                               messages=messages,
                               # 设置随机数种子seed，如果没有设置，则随机数种子默认为1234
                               seed=random.randint(1, 10000),
                               # 将输出设置为"message"格式
                               result_format='message')
    print(response)
    return JSONResponse(response.output.choices[0]['message']['content'])


# 请求处理函数
async def predict_glm(request):
    query_params = await request.json()
    prompt = query_params["prompt"]
    response, history = model.chat(tokenizer, prompt)
    print(response)
    return JSONResponse(response)


# 创建路由列表
routes = [
    Route("/qwen", endpoint=predict_qwen),  # 路由到/qwen
    Route("/glm", endpoint=predict_glm)  # 路由到/glm
]


# 创建Starlette应用程序
app = Starlette(debug=False, routes=routes)


# 启动应用程序
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8848, log_level="info")
