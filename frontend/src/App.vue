<template>
  <div v-if="!isLoggedIn" class="login-page">
    <Login @login-success="handleLoginSuccess" />
  </div>
  <el-container v-else class="app-container">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarCollapsed ? '64px' : '200px'" class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="logo" @click="toggleSidebar">
        <span v-if="!sidebarCollapsed">Emby 管理系统</span>
        <el-icon v-else><Menu /></el-icon>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical-demo"
        mode="vertical"
        :default-openeds="['1']"
        unique-opened
        @select="handleMenuSelect"
        :collapse="sidebarCollapsed"
        active-text-color="#ffffff"
        background-color="#1989fa"
        text-color="rgba(255, 255, 255, 0.9)"
      >
        <el-menu-item index="1">
          <el-icon><User /></el-icon>
          <template #title>
            <span>用户管理</span>
          </template>
        </el-menu-item>
        <el-menu-item index="2">
          <el-icon><AlarmClock /></el-icon>
          <template #title>
            <span>检查过期用户</span>
          </template>
        </el-menu-item>
        <el-menu-item index="3">
          <el-icon><Connection /></el-icon>
          <template #title>
            <span>检查 Emby 连接</span>
          </template>
        </el-menu-item>
        <el-menu-item index="4">
          <el-icon><VideoCamera /></el-icon>
          <template #title>
            <span>189Share 管理</span>
          </template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <el-button type="text" @click="toggleSidebar" class="sidebar-toggle">
            <el-icon><Menu /></el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-actions">
          <el-dropdown>
            <el-button type="info" round>
              <el-icon><User /></el-icon>
              <span>用户</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <!-- 搜索区域 -->
        <el-card class="search-card" v-if="activeMenu === '1'">
          <el-form :inline="true" :model="searchForm" class="search-form">
            <el-form-item>
              <el-input
                v-model="searchQuery"
                placeholder="搜索用户名"
                style="width: 280px"
                clearable
                prefix-icon="Search"
              />
            </el-form-item>
            <el-form-item>
              <el-select
                v-model="statusFilter"
                placeholder="选择状态"
                style="width: 140px"
                clearable
              >
                <el-option label="启用" :value="true" />
                <el-option label="禁用" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-select
                v-model="expireFilter"
                placeholder="选择过期状态"
                style="width: 140px"
                clearable
              >
                <el-option label="未过期" :value="'active'" />
                <el-option label="已过期" :value="'expired'" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="fetchUsers">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
            </el-form-item>
          </el-form>
          <div class="action-buttons-section" style="margin-top: 16px; display: flex; gap: 12px;">
            <el-button type="primary" @click="openCreateUserDialog" round>
              <el-icon><Plus /></el-icon>
              创建用户
            </el-button>
            <el-button type="success" @click="syncUsers" round>
              <el-icon><Refresh /></el-icon>
              同步Emby用户
            </el-button>
          </div>
        </el-card>

        <!-- 用户列表 -->
        <el-card class="user-list-card" v-if="activeMenu === '1'">
          <template #header>
            <div class="card-header">
              <span>用户列表</span>
              <span class="user-count">(共 {{ users.length }} 个用户)</span>
            </div>
          </template>
          <el-table :data="paginatedUsers" style="width: 100%" v-loading="loading" stripe>
            <el-table-column prop="emby_id" label="Emby ID" min-width="280" />
            <el-table-column prop="name" label="用户名" min-width="140" />
            <el-table-column prop="created_at" label="注册时间" min-width="180">
              <template #default="scope">
                {{ scope.row.created_at }}
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" min-width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'" effect="light">
                  {{ scope.row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="expire_date" label="过期时间" min-width="160">
              <template #default="scope">
                <span :class="{ 'expired': scope.row.expire_date && new Date(scope.row.expire_date) < new Date() }">
                  {{ scope.row.expire_date ? scope.row.expire_date : '永久' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="220" fixed="right">
              <template #default="scope">
                <div class="action-buttons">
                  <!-- 检查是否为受保护用户 -->
                  <template v-if="['emby_tpl_user', 'huxt', 'test'].includes(scope.row.name)">
                    <el-button size="small" disabled class="action-btn" link>
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-button>
                    <el-button
                      size="small"
                      :type="scope.row.is_active ? 'warning' : 'success'"
                      disabled
                      class="action-btn"
                    >
                      <el-icon v-if="scope.row.is_active"><Close /></el-icon>
                      <el-icon v-else><Check /></el-icon>
                      {{ scope.row.is_active ? '禁用' : '启用' }}
                    </el-button>
                    <el-button size="small" type="danger" disabled class="action-btn" link>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </template>
                  <template v-else>
                    <el-button size="small" @click="openEditUserDialog(scope.row)" class="action-btn" type="primary" link>
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-button>
                    <el-button
                      size="small"
                      :type="scope.row.is_active ? 'warning' : 'success'"
                      @click="toggleUserStatus(scope.row)"
                      class="action-btn"
                    >
                      <el-icon v-if="scope.row.is_active"><Close /></el-icon>
                      <el-icon v-else><Check /></el-icon>
                      {{ scope.row.is_active ? '禁用' : '启用' }}
                    </el-button>
                    <el-button size="small" type="danger" @click="deleteUser(scope.row.id)" class="action-btn" link>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </template>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination" v-if="users.length > 0">
            <el-pagination
              layout="prev, pager, next"
              :total="users.length"
              :page-size="10"
              @current-change="handleCurrentChange"
              style="margin-top: 20px; text-align: right"
            />
          </div>
        </el-card>

        <!-- 检查过期用户 -->
        <div v-if="activeMenu === '2'" class="full-width-content">
          <el-card class="expire-card" shadow="hover" style="width: 100%;">
            <template #header>
              <div class="card-header">
                <span>检查过期用户</span>
              </div>
            </template>
            <div class="expire-content">
              <p>点击下方按钮检查并禁用过期用户</p>
              <el-button type="primary" @click="checkExpiredUsers" size="large">
                <el-icon><AlarmClock /></el-icon>
                检查过期
              </el-button>
            </div>
          </el-card>
        </div>

        <!-- 检查 Emby 连接 -->
        <div v-if="activeMenu === '3'" class="full-width-content">
          <el-card class="connection-card" shadow="hover" style="width: 100%;">
            <template #header>
              <div class="card-header">
                <span>检查 Emby 连接</span>
              </div>
            </template>
            <div class="connection-content">
              <p>点击下方按钮检查与 Emby 服务器的连接状态</p>
              <el-button type="primary" @click="checkEmbyConnection" size="large">
                <el-icon><Connection /></el-icon>
                检查连接
              </el-button>
              <div v-if="connectionStatus" class="connection-result">
                <el-alert
                  :title="connectionStatus.connected ? '连接成功' : '连接失败'"
                  :type="connectionStatus.connected ? 'success' : 'error'"
                  :description="connectionStatus.message"
                  show-icon
                  style="margin-top: 20px"
                />
                <el-card v-if="connectionStatus.connected && connectionStatus.server_info" class="server-info-card" style="margin-top: 20px" shadow="hover">
                  <template #header>
                    <div class="card-header">
                      <span>Emby 服务器信息</span>
                    </div>
                  </template>
                  <el-descriptions :column="1" border>
                    <el-descriptions-item label="服务器名称">{{ connectionStatus.server_info.name }}</el-descriptions-item>
                    <el-descriptions-item label="版本">{{ connectionStatus.server_info.version }}</el-descriptions-item>
                    <el-descriptions-item label="操作系统">{{ connectionStatus.server_info.operating_system }}</el-descriptions-item>
                  </el-descriptions>
                </el-card>
              </div>
            </div>
          </el-card>
        </div>

        <!-- CloudPan 189Share 管理 -->
        <div v-if="activeMenu === '4'" class="full-width-content">
          <el-card class="cloudpan189share-card" shadow="hover" style="width: 100%;">
            <template #header>
              <div class="card-header">
                <span>189Share 管理</span>
              </div>
            </template>
            <div class="cloudpan189share-content">
              <div class="action-buttons">
                <el-button type="primary" @click="executeCloudPan189ShareScript" size="large">
                  <el-icon><VideoCamera /></el-icon>
                  执行 CloudPan 189Share 脚本
                </el-button>
                <el-button type="success" @click="fetchCloudPan189ShareLogs" size="large">
                  <el-icon><Document /></el-icon>
                  刷新日志
                </el-button>
                <el-button type="danger" @click="stopCloudPan189ShareScript" size="large">
                  <el-icon><Close /></el-icon>
                  中断执行
                </el-button>
              </div>
              <div class="logs-section" style="margin-top: 20px;">
                <el-card class="logs-card" shadow="hover">
                  <template #header>
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                      <span>执行日志</span>
                      <el-switch 
                        v-model="autoScrollEnabled" 
                        active-text="自动滚动" 
                        inactive-text="手动滚动"
                        style="margin-left: 10px;"
                      />
                    </div>
                  </template>
                  <div class="logs-container" v-loading="loadingCloudPanLogs">
                    <el-scrollbar height="400px" ref="scrollbarRef">
                      <pre v-if="cloudpan189shareLogs" class="logs-content">{{ cloudpan189shareLogs }}</pre>
                      <div v-else class="no-logs">
                        脚本尚未执行或日志文件不存在
                      </div>
                    </el-scrollbar>
                  </div>
                </el-card>
              </div>
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="createUserDialogVisible"
      title="创建用户"
      width="500px"
      center
    >
      <el-form :model="createUserForm" :rules="createUserRules" ref="createUserFormRef">
        <el-form-item label="用户名" prop="name">
          <el-input v-model="createUserForm.name" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createUserForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="createUserForm.expire_date"
            type="datetime"
            placeholder="选择过期时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createUserDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createUser">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="editUserDialogVisible"
      title="编辑用户"
      width="500px"
      center
    >
      <el-form :model="editUserForm" ref="editUserFormRef">
        <el-form-item label="用户名">
          <el-input v-model="editUserForm.name" disabled />
        </el-form-item>
        <el-form-item label="状态">
          <el-tag :type="editUserForm.is_active ? 'success' : 'danger'" effect="light">
            {{ editUserForm.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="过期时间" required>
          <el-date-picker
            v-model="editUserForm.expire_date"
            type="datetime"
            placeholder="选择过期时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
            format="YYYY-MM-D HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editUserDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="updateUser">保存</el-button>
        </span>
      </template>
    </el-dialog>

  </el-container>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import Login from './components/Login.vue'

// 配置 axios 基础路径
axios.defaults.baseURL = '/api'

// 添加请求拦截器，携带token
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 添加响应拦截器，处理401错误
axios.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response && error.response.status === 401) {
      // 检查是否是登录接口的请求
      const isLoginRequest = error.config && error.config.url && error.config.url.includes('/login')
      if (!isLoginRequest) {
        // 清除本地存储的登录状态
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        // 重新加载页面，跳转到登录页
        window.location.reload()
      }
    }
    return Promise.reject(error)
  }
)

export default {
  name: 'App',
  components: {
    Login
  },
  setup() {
    // 响应式数据
    const isLoggedIn = ref(false)
    const activeMenu = ref('1')
    const users = ref([])
    const createUserDialogVisible = ref(false)
    const editUserDialogVisible = ref(false)
    const connectionStatus = ref(null)
    const searchQuery = ref('')
    const statusFilter = ref(null)
    const expireFilter = ref(null)
    const loading = ref(false)
    const sidebarCollapsed = ref(false)
    const searchForm = ref({})
    const currentPage = ref(1)
    const cloudpan189shareLogs = ref('')
    const loadingCloudPanLogs = ref(false)
    const autoScrollEnabled = ref(true)
    const scrollbarRef = ref(null)
    
    // 检查登录状态
    const checkLoginStatus = () => {
      const token = localStorage.getItem('token')
      isLoggedIn.value = !!token
    }
    
    // 处理登录成功
    const handleLoginSuccess = () => {
      checkLoginStatus()
      fetchUsers()
    }
    
    // 处理退出登录
    const handleLogout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      isLoggedIn.value = false
      ElMessage.success('已退出登录')
    }

    // 表单数据
    const createUserForm = ref({
      name: '',
      password: '123456',
      expire_date: null
    })

    const editUserForm = ref({
      id: '',
      name: '',
      password: '',
      email: '',
      is_active: true,
      expire_date: null
    })

    // 表单验证规则
    const createUserRules = {
      name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
    }

    const editUserRules = {
      name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      email: [{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }]
    }

    // 表单引用
    const createUserFormRef = ref(null)
    const editUserFormRef = ref(null)

    // 计算属性
    const pageTitle = computed(() => {
      switch (activeMenu.value) {
        case '1': return '用户管理'
        case '2': return '检查过期用户'
        case '3': return '检查 Emby 连接'
        case '4': return '189Share 管理'
        default: return '用户管理'
      }
    })

    const paginatedUsers = computed(() => {
      const pageSize = 10
      const startIndex = (currentPage.value - 1) * pageSize
      const endIndex = startIndex + pageSize
      return users.value.slice(startIndex, endIndex)
    })

    // 方法
    const handleMenuSelect = (key) => {
      activeMenu.value = key
    }

    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    const fetchUsers = async () => {
      try {
        loading.value = true
        // 构建请求参数
        const params = {}
        if (searchQuery.value) {
          params.search = searchQuery.value
        }
        if (statusFilter.value !== null && statusFilter.value !== undefined) {
          params.status = statusFilter.value
        }
        if (expireFilter.value !== null && expireFilter.value !== undefined) {
          params.expire_status = expireFilter.value
        }
        const response = await axios.get('/users', { params })
        if (response.data.success) {
          users.value = response.data.data
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '获取用户列表失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    const openCreateUserDialog = () => {
      createUserForm.value = {
        name: '',
        password: '123456',
        expire_date: null
      }
      createUserDialogVisible.value = true
    }

    const createUser = async () => {
      if (!createUserFormRef.value) return
      
      try {
        loading.value = true
        await createUserFormRef.value.validate()
        const response = await axios.post('/users', createUserForm.value)
        if (response.data.success) {
          ElMessage.success('用户创建成功')
          createUserDialogVisible.value = false
          fetchUsers()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '创建用户失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    const openEditUserDialog = (user) => {
      editUserForm.value = {
        id: user.id,
        name: user.name,
        password: '',
        email: user.email,
        is_active: user.is_active,
        expire_date: user.expire_date ? user.expire_date : null
      }
      console.log('编辑用户对话框打开，用户数据:', user)
      console.log('编辑用户对话框打开，过期时间:', editUserForm.value.expire_date)
      editUserDialogVisible.value = true
    }

    const updateUser = async () => {
      if (!editUserFormRef.value) return
      
      try {
        loading.value = true
        await editUserFormRef.value.validate()
        const response = await axios.put(`/users/${editUserForm.value.id}`, editUserForm.value)
        if (response.data.success) {
          ElMessage.success('用户更新成功')
          editUserDialogVisible.value = false
          fetchUsers()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '更新用户失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    const toggleUserStatus = async (user) => {
      try {
        loading.value = true
        const response = await axios.put(`/users/${user.id}/status`, {
          is_active: !user.is_active
        })
        if (response.data.success) {
          ElMessage.success(`用户已${!user.is_active ? '启用' : '禁用'}`)
          fetchUsers()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '操作失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    const deleteUser = async (userId) => {
      try {
        await ElMessageBox.confirm('确定要删除该用户吗？', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        loading.value = true
        const response = await axios.delete(`/users/${userId}`)
        if (response.data.success) {
          ElMessage.success('用户删除成功')
          fetchUsers()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        if (error !== 'cancel') {
          const errorMessage = error.response?.data?.message || '删除用户失败'
          ElMessage.error(errorMessage)
          console.error(error)
        }
      } finally {
        loading.value = false
      }
    }

    const syncUsers = async () => {
      try {
        loading.value = true
        const response = await axios.post('/sync/users')
        if (response.data.success) {
          ElMessage.success(response.data.message)
          fetchUsers()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '同步失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    const checkExpiredUsers = async () => {
      try {
        loading.value = true
        const response = await axios.post('/check-expire')
        if (response.data.success) {
          ElMessage.success(response.data.message)
          fetchUsers()
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '检查失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    const checkEmbyConnection = async () => {
      try {
        loading.value = true
        const response = await axios.get('/emby/check-connection')
        if (response.data.success) {
          connectionStatus.value = {
            connected: response.data.connected,
            message: response.data.message,
            server_info: response.data.server_info
          }
        } else {
          const errorMessage = response.data.message || '检查连接状态失败'
          ElMessage.error(errorMessage)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '检查连接失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    // 执行CloudPan 189Share脚本
    const executeCloudPan189ShareScript = async () => {
      try {
        loading.value = true
        const response = await axios.post('/189share/execute')
        if (response.data.success) {
          ElMessage.success(response.data.message)
          // 执行后自动获取日志
          setTimeout(() => {
            fetchCloudPan189ShareLogs()
          }, 2000)
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '执行脚本失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    // 获取CloudPan 189Share脚本执行日志
    const fetchCloudPan189ShareLogs = async () => {
      try {
        loadingCloudPanLogs.value = true
        const response = await axios.get('/189share/logs')
        if (response.data.success) {
          cloudpan189shareLogs.value = response.data.logs
          console.log('获取到的日志内容:', response.data.logs)
          
          // 自动滚动到底部
          if (autoScrollEnabled.value) {
            setTimeout(() => {
              if (scrollbarRef.value) {
                scrollbarRef.value.wrap.scrollTop = scrollbarRef.value.wrap.scrollHeight
              }
            }, 100)
          }
        } else {
          ElMessage.error(response.data.message)
          console.error('获取日志失败:', response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '获取日志失败'
        ElMessage.error(errorMessage)
        console.error('获取日志时发生错误:', error)
      } finally {
        loadingCloudPanLogs.value = false
      }
    }

    // 中断CloudPan 189Share脚本执行
    const stopCloudPan189ShareScript = async () => {
      try {
        loading.value = true
        const response = await axios.post('/189share/stop')
        if (response.data.success) {
          ElMessage.success(response.data.message)
          // 中断后刷新日志
          setTimeout(() => {
            fetchCloudPan189ShareLogs()
          }, 1000)
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '中断脚本失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    // 生命周期
    onMounted(() => {
      checkLoginStatus()
      if (isLoggedIn.value) {
        fetchUsers()
      }
    })

    return {
      isLoggedIn,
      activeMenu,
      users,
      paginatedUsers,
      pageTitle,
      createUserDialogVisible,
      editUserDialogVisible,
      connectionStatus,
      createUserForm,
      editUserForm,
      createUserRules,
      editUserRules,
      createUserFormRef,
      editUserFormRef,
      searchQuery,
      statusFilter,
      expireFilter,
      loading,
      sidebarCollapsed,
      searchForm,
      currentPage,
      cloudpan189shareLogs,
      loadingCloudPanLogs,
      handleMenuSelect,
      toggleSidebar,
      handleCurrentChange,
      formatDate,
      fetchUsers,
      openCreateUserDialog,
      createUser,
      openEditUserDialog,
      updateUser,
      toggleUserStatus,
      deleteUser,
      syncUsers,
      checkExpiredUsers,
      checkEmbyConnection,
      executeCloudPan189ShareScript,
      fetchCloudPan189ShareLogs,
      stopCloudPan189ShareScript,
      autoScrollEnabled,
      scrollbarRef,
      handleLoginSuccess,
      handleLogout
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body, html {
  width: 100%;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

#app {
  width: 100%;
  height: 100vh;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  width: 100%;
  max-width: 100vw;
  background-color: #f0f2f5;
}

/* 侧边栏样式 */
.sidebar {
  background-color: #1989fa;
  color: #fff;
  transition: all 0.3s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px !important;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 16px;
  font-weight: bold;
  background-color: #1989fa;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sidebar.collapsed .logo {
  font-size: 20px;
}

.el-menu-vertical-demo {
  height: calc(100% - 60px);
  border-right: none;
  background-color: #1989fa;
}

.el-menu-item {
  color: rgba(255, 255, 255, 0.9);
  height: 50px;
  line-height: 50px;
  font-size: 14px;
  margin: 0 !important;
  transition: all 0.3s ease;
}

.el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}

.el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.3) !important;
  color: white !important;
}

/* 页面头部样式 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  height: 60px;
  transition: all 0.3s ease;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sidebar-toggle {
  margin-right: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 面包屑导航样式 */
.el-breadcrumb {
  font-size: 14px;
}

.el-breadcrumb__item:last-child {
  color: #1989fa;
  font-weight: 500;
}

/* 主内容区样式 */
.main-content {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 120px);
}

/* 搜索卡片样式 */
.search-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
  border-radius: 8px;
}

.search-form {
  width: 100%;
}

/* 用户列表卡片样式 */
.user-list-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  overflow: hidden;
}

/* 表格样式 */
.el-table {
  width: 100% !important;
  border-radius: 8px;
  overflow: hidden;
}

.el-table--striped .el-table__row--striped {
  background-color: #fafafa;
}

.el-table th {
  background-color: #f5f7fa;
  font-weight: 500;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-btn {
  margin: 0 !important;
}

/* 居中内容样式 */
.center-content {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px);
}

/* 全屏宽度内容样式 */
.full-width-content {
  width: 100%;
  min-height: calc(100vh - 120px);
}

/* 卡片样式 */
.expire-card,
.connection-card {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.expire-card:hover,
.connection-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.expire-content,
.connection-content {
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 40px;
}

.expire-content p,
.connection-content p {
  font-size: 18px;
  color: #495057;
  margin-bottom: 0;
  line-height: 1.6;
  max-width: 600px;
}

/* 按钮样式增强 */
.expire-content .el-button,
.connection-content .el-button {
  padding: 14px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 50px;
  transition: all 0.3s ease;
}

.expire-content .el-button:hover,
.connection-content .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.3);
}

/* 服务器信息卡片样式 */
.server-info-card {
  margin-top: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.server-info-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

/* 服务器信息描述列表样式 */
.server-info-card .el-descriptions {
  padding: 20px;
}

.server-info-card .el-descriptions__label {
  font-weight: 600;
  color: #495057;
}

.server-info-card .el-descriptions__content {
  color: #6c757d;
}

/* 对话框样式 */
.el-dialog__header {
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 过期时间样式 */
.expired {
  color: #f56c6c;
  font-weight: 500;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }

  .sidebar {
    width: 100% !important;
    height: auto;
  }

  .el-menu-vertical-demo {
    display: flex;
    height: auto;
    flex-direction: row;
    overflow-x: auto;
  }

  .el-menu-item {
    flex: 1;
    text-align: center;
    height: 45px;
    line-height: 45px;
    white-space: nowrap;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 10px;
    height: auto;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .main-content {
    padding: 10px;
    min-height: calc(100vh - 160px);
  }

  .search-form {
    flex-direction: column;
    align-items: flex-start;
  }

  .expire-card,
  .connection-card {
    width: 100%;
    margin: 0;
  }

  .expire-content,
  .connection-content {
    padding: 20px;
  }

  .action-buttons {
    width: 100%;
    justify-content: space-between;
  }

  .el-button {
    font-size: 12px;
    padding: 8px 12px;
  }
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 加载状态样式 */
.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* CloudPan 189Share 管理页面样式 */
.cloudpan189share-card {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.cloudpan189share-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.cloudpan189share-content {
  padding: 30px;
}

.action-buttons {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.action-buttons .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.logs-card {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.logs-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.logs-container {
  width: 100%;
}

.logs-content {
  font-family: 'Courier New', Courier, monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.no-logs {
  text-align: center;
  color: #909399;
  padding: 40px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}
</style>