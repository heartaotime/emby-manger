@echo off

REM Emby Manager Docker Image Push Script

REM Image name and tag
set imageName=emby-manager
set dockerHubUsername=heartaotime
set tag=latest

REM Build image
echo Building Docker image...
docker build -t %imageName% .

if %errorlevel% == 0 (
    echo Image built successfully!
    
    REM Tag image
    echo Tagging image...
    docker tag %imageName% %dockerHubUsername%/%imageName%:%tag%
    
    if %errorlevel% == 0 (
        echo Image tagged successfully!
        
        REM Prompt user to login to Docker Hub
        echo Please make sure you are logged in to Docker Hub.
        echo Run 'docker login' if you haven't logged in yet.
        echo.
        @REM pause
        
        REM Push image
        echo Pushing image to Docker Hub...
        docker push %dockerHubUsername%/%imageName%:%tag%
        
        if %errorlevel% == 0 (
            echo Image pushed successfully!
            echo Image URL: %dockerHubUsername%/%imageName%:%tag%
        ) else (
            echo Failed to push image. Please check your Docker Hub login status and network connection.
        )
    ) else (
        echo Failed to tag image. Please check your Docker command.
    )
) else (
    echo Failed to build image. Please check your Dockerfile and project structure.
)

echo Script completed.
@REM pause
