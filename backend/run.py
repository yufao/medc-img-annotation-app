import os
from app import create_app

# 让 Flask 的 static 路由指向 app/static 目录
static_folder = os.path.join(os.path.dirname(__file__), 'app', 'static')
app = create_app(static_folder=static_folder)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
