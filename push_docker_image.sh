#!/bin/bash

# Emby管理系统Docker镜像推送脚本

# 镜像名称和标签
imageName="emby-manager"
dockerHubUsername="heartaotime"  # 请替换为你的Docker Hub用户名
tag="latest"

# 构建镜像
echo "开始构建Docker镜像..."
docker build -t $imageName .

if [ $? -eq 0 ]; then
    echo "镜像构建成功！"
    
    # 标记镜像
    echo "开始标记镜像..."
    docker tag $imageName "$dockerHubUsername/$imageName:$tag"
    
    if [ $? -eq 0 ]; then
        echo "镜像标记成功！"
        
        # 提示用户登录Docker Hub
        echo "请确保你已经登录Docker Hub，执行以下命令登录："
        echo "docker login"
        echo ""
        read -p "登录完成后按Enter键继续..."
        
        # 推送镜像
        echo "开始推送镜像到Docker Hub..."
        docker push "$dockerHubUsername/$imageName:$tag"
        
        if [ $? -eq 0 ]; then
            echo "镜像推送成功！"
            echo "镜像地址：$dockerHubUsername/$imageName:$tag"
        else
            echo "镜像推送失败，请检查Docker Hub登录状态和网络连接。"
        fi
    else
        echo "镜像标记失败，请检查Docker命令是否正确。"
    fi
else
    echo "镜像构建失败，请检查Dockerfile和项目结构。"
fi

echo "脚本执行完成。"
