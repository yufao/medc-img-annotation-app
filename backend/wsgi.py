import os
from app import create_app

# 获取环境配置
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == "__main__":
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )