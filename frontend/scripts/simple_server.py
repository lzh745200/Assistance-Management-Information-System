# !/usr/bin/env python3# -*- coding: utf-8 -*-"""简单的Python HTTP服务器，用于托管前端文件确保系统
在
离线环境下也能正常访问"""
# 服务器配置PORT = 3000HOST = "localhost"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):    """自定义

请求处理器，添加CORS支持和友好的日志输出"""
    def end_headers(self):        # 添加CORS支持        self.send_header(
    'Access-Control-Allow-Origin',
'*')        self.send_header('Access-Control
-Allow-Methods',
'GET, OPTIONS')        self.send_header('Access-Control-Allow-
Headers', 'Content-Type')        super().end_headers()
    def log_message(self,
format, *args):        # 简化日志输出        current_time =
 time.strftime('%Y-%m-%d %H:%M:%S')        print(f"[{current_time}] {self.clien
t_address[0]} - {format % args}")
    # 自定义错误页面    def error_message_format(
    self):        return """<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN"><
html><head>    <title>军事乡村振兴系统 - %(code)d %(message)s</title>    <style>
 body { font-family: 'Microsoft YaHei',
Arial,
sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color
: #f4f4f4; color: #333; }        .container { max-width: 600px; margin: 0 auto;
 background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }        h1 { color: #e63946; }    </style></head><body>    <div class="container">        <h1>%(code)d %(message)s</h1>        <p>抱歉，您请求的资源无法访问。</p>        <p><a href="/">返回首页</a> | <a href="/login.html">返回登录页</a></p>    </div></body></html>"""

def run_server():    """启动HTTP服务器"""    # 确保在当前目录下运行    os.chdir(

    os.path.dirname(os.path.abspath(__file__)))
    # 创建请求处理器    handler = CustomHTTPRequestHandler
    # 创建服务器实例    try:        with socketserver.TCPServer((HOST, PORT),
     handler) as httpd:            print("=" * 60)            print("军事乡村振兴系统 -
 单机版服务器")            print("=" * 60)            print(f"服务器运行在: http://{HOST}:{
PORT}")            print("")            print("访问地址:")            print("  登录页
面: http://{HOST}:{PORT}/login.html")            print(f"  系统主页: http://{HOST}:{PORT}/index.html")            print("")            print("提示:")            print("  1. 系统已配置为离线模式，将使用本地验证进行登录")            print("  2. 默认账号: admin / 123456")            print("  3. 按 Ctrl+C 停止服务器")            print("=" * 60)
            # 尝试自动打开浏览器            try:                login_url = f"http://{HO
ST}:{PORT}/login.html"                print(f"正在打开浏览器访问登录页面: {login_url}")
           webbrowser.open(login_url)            except Exception as e:
        print(f"无法自动打开浏览器: {e}")                print("请手动在浏览器中输入上述地址访问系统")
            # 启动服务器            httpd.serve_forever()
    except OSError as e:        if "Address already in use" in str(
    e):            print(f"错误: 端口 {PORT} 已被占用")            print("请关闭占用该端口的程序，或
修改本脚本中的PORT变量")        else:            print(f"服务器启动失败: {e}")        sys.exit(
1)    except KeyboardInterrupt:        print("\n服务器已停止")        sys.exit(0)
except Exception as e:        print(f"未知错误: {e}")        sys.exit(1)

if __name__ == "__main__":    run_server()
