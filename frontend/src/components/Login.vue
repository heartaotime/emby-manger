<template>
  <div class="login-container">
    <div class="login-form">
      <h2 class="login-title">Emby 管理系统</h2>
      <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 使用相对路径，与App.vue保持一致
// axios.defaults.baseURL = '/api'

export default {
  name: 'Login',
  setup(props, { emit }) {
    const loginForm = ref({
      username: '',
      password: ''
    })

    const loginFormRef = ref(null)
    const loading = ref(false)

    const loginRules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
    }

    const handleLogin = async () => {
      if (!loginFormRef.value) return
      
      try {
        await loginFormRef.value.validate()
        loading.value = true
        console.log('发送登录请求:', loginForm.value)
        
        const response = await axios.post('/api/auth/login', loginForm.value)
        console.log('登录响应:', response)
        if (response.data.success) {
          // 存储token到localStorage
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('user', JSON.stringify(response.data.user))
          
          ElMessage.success('登录成功')
          emit('login-success')
        } else {
          console.log('登录失败（非401）:', response.data)
          ElMessage.error(response.data.message || '登录失败')
        }
      } catch (error) {
        console.error('登录错误:', error)
        console.log('错误详情:', {
          response: error.response,
          request: error.request,
          message: error.message
        })
        let errorMessage = '登录失败'
        
        if (error.response) {
          // 服务器返回错误响应
          console.log('服务器返回错误:', {
            status: error.response.status,
            data: error.response.data
          })
          if (error.response.status === 401) {
            errorMessage = error.response.data?.message || '用户名或密码错误'
          } else {
            errorMessage = error.response.data?.message || `服务器错误 (${error.response.status})`
          }
        } else if (error.request) {
          // 请求已发送但没有收到响应
          errorMessage = '无法连接到服务器，请检查网络连接'
        } else {
          // 请求配置出错
          errorMessage = `请求错误: ${error.message}`
        }
        
        console.log('准备显示错误信息:', errorMessage)
        ElMessage.error(errorMessage)
      } finally {
        loading.value = false
      }
    }

    return {
      loginForm,
      loginFormRef,
      loading,
      loginRules,
      handleLogin
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
  background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-form {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  transition: all 0.3s ease;
}

.login-form:hover {
  box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.5);
  transform: translateY(-5px);
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
  font-size: 24px;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 输入框样式 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper):hover {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
}

/* 按钮样式 */
:deep(.el-button--primary) {
  border-radius: 8px;
  padding: 12px;
  font-size: 16px;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

:deep(.el-button--primary):hover {
  background: linear-gradient(135deg, #5a6fe8 0%, #6a409a 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

:deep(.el-button--primary):active {
  transform: translateY(2px);
}

/* 错误提示样式 */
:deep(.el-form-item__error) {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-form {
    padding: 30px 20px;
    margin: 0 10px;
  }
  
  .login-title {
    font-size: 20px;
  }
}
</style>