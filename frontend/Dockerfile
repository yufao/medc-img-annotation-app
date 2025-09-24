# 前端Docker镜像构建文件
# 优化版本 - 避免网络问题和buildx错误

# 构建阶段 - 使用本地构建结果
FROM nginx:1.21-alpine

# 复制本地构建好的静态文件
COPY dist/ /usr/share/nginx/html/

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 设置权限
RUN chmod -R 755 /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
