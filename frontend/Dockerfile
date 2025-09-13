# 前端Docker镜像构建文件
# 使用本地已安装的node_modules进行构建，避免网络问题

# 构建阶段
FROM node:18-alpine AS build

WORKDIR /app

# 复制所有文件，包括已经安装好的 node_modules
COPY . .

# 确保有执行权限并构建应用
RUN npm run build

# 生产阶段
FROM nginx:1.21-alpine

# 复制构建结果到nginx
COPY --from=build /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
