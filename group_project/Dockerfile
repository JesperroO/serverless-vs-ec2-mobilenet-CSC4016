FROM public.ecr.aws/lambda/python:3.8

# 把我们干净的代码复制进去
COPY model_loader.py ./
COPY app.py ./

# CMD 必须指向 <文件名>.<处理器函数名>
CMD [ "app.handler" ]