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
        <el-menu-item index="5">
          <el-icon><Document /></el-icon>
          <template #title>
            <span>日志管理</span>
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
              <span class="user-count">(共 {{ totalUsers }} 个用户)</span>
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
          <div class="pagination" v-if="totalUsers > 0">
            <div class="pagination-controls">
              <div class="page-size-selector">
                <el-select v-model="pageSize" @change="handlePageSizeChange" style="width: 120px;">
                  <el-option label="10条/页" :value="10" />
                  <el-option label="20条/页" :value="20" />
                  <el-option label="50条/页" :value="50" />
                  <el-option label="100条/页" :value="100" />
                  <el-option label="自定义" :value="'custom'" />
                </el-select>
                <el-input-number v-if="pageSize === 'custom'" v-model="customPageSize" @change="handleCustomPageSizeChange" :min="1" :max="1000" style="width: 100px; margin-left: 10px;" />
              </div>
              <el-pagination
                layout="prev, pager, next, jumper"
                :total="totalUsers"
                v-model:current-page="currentPage"
                :page-size="actualPageSize"
                @current-change="handleCurrentChange"
                :pager-count="5"
                hide-on-single-page
              />
            </div>
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

        <!-- 日志管理 -->
        <div v-if="activeMenu === '5'" class="full-width-content">
          <el-card class="logs-management-card" shadow="hover" style="width: 100%;">
            <template #header>
              <div class="card-header">
                <span>日志管理</span>
              </div>
            </template>
            <div class="logs-management-content">
              <div class="logs-controls" style="margin-bottom: 20px; display: flex; gap: 16px; align-items: center;">
                <el-form :inline="true" :model="logsForm" class="logs-form">
                  <el-form-item label="日志类型">
                    <el-radio-group v-model="logsForm.logType" @change="handleLogTypeChange">
                      <el-radio label="all">所有日志</el-radio>
                      <el-radio label="plugin">插件日志</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="插件选择" v-if="logsForm.logType === 'plugin'">
                    <el-select v-model="logsForm.pluginName" placeholder="选择插件" style="width: 200px;">
                      <el-option v-for="plugin in availablePlugins" :key="plugin" :label="plugin" :value="plugin" />
                    </el-select>
                  </el-form-item>
                </el-form>
                <el-button type="primary" @click="fetchLogs" size="large">
                  <el-icon><Refresh /></el-icon>
                  刷新日志
                </el-button>
                <el-button type="danger" @click="clearLogs" size="large">
                  <el-icon><Delete /></el-icon>
                  清理日志
                </el-button>
              </div>
              <div class="logs-section" style="margin-top: 20px;">
                <el-card class="logs-card" shadow="hover">
                  <template #header>
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                      <span>{{ logsForm.logType === 'all' ? '所有日志' : `${logsForm.pluginName || '插件'}日志` }}</span>
                      <el-switch 
                        v-model="logsAutoScrollEnabled" 
                        active-text="自动滚动" 
                        inactive-text="手动滚动"
                        style="margin-left: 10px;"
                      />
                    </div>
                  </template>
                  <div class="logs-container" v-loading="loadingLogs">
                    <el-scrollbar height="500px" ref="logsScrollbarRef">
                      <pre v-if="logsContent" class="logs-content">{{ logsContent }}</pre>
                      <div v-else class="no-logs">
                        {{ logsForm.logType === 'all' ? '暂无日志' : '请选择插件并刷新日志' }}
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
// axios.defaults.baseURL = '/api'

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
    const pageSize = ref(10)
    const customPageSize = ref(10)
    const cloudpan189shareLogs = ref('')
    const loadingCloudPanLogs = ref(false)
    const autoScrollEnabled = ref(true)
    const scrollbarRef = ref(null)
    
    // 日志管理相关数据
    const logsForm = ref({
      logType: 'all',
      pluginName: ''
    })
    const logsContent = ref('')
    const loadingLogs = ref(false)
    const logsAutoScrollEnabled = ref(true)
    const logsScrollbarRef = ref(null)
    const availablePlugins = ref([])
    
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
        case '5': return '日志管理'
        default: return '用户管理'
      }
    })

    const paginatedUsers = computed(() => {
      const startIndex = (currentPage.value - 1) * (pageSize.value === 'custom' ? customPageSize.value : pageSize.value)
      const endIndex = startIndex + (pageSize.value === 'custom' ? customPageSize.value : pageSize.value)
      return users.value.slice(startIndex, endIndex)
    })

    const actualPageSize = computed(() => {
      return pageSize.value === 'custom' ? customPageSize.value : pageSize.value
    })

    const handlePageSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1 // 重置为第一页
      fetchUsers() // 重新获取用户列表
    }

    const handleCustomPageSizeChange = (size) => {
      if (size && size > 0) {
        customPageSize.value = size
        currentPage.value = 1 // 重置为第一页
        fetchUsers() // 重新获取用户列表
      }
    }

    // 方法
    const handleMenuSelect = (key) => {
      // 切换菜单时关闭SSE连接
      if (key !== '4') {
        closeSSEConnection()
      }
      // 切换菜单时关闭日志SSE连接
      if (key !== '5') {
        closeLogsSSEConnection()
      }
      activeMenu.value = key
      // 切换到189share管理页面时建立SSE连接
      if (key === '4') {
        establishSSEConnection()
      }
      // 切换到日志管理页面时建立SSE连接
      if (key === '5') {
        establishLogsSSEConnection()
      }
    }

    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
      fetchUsers() // 重新获取用户列表
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    const totalUsers = ref(0)

    const fetchUsers = async () => {
      try {
        loading.value = true
        // 构建请求参数
        const params = {
          page: currentPage.value,
          page_size: actualPageSize.value
        }
        if (searchQuery.value) {
          params.search = searchQuery.value
        }
        if (statusFilter.value !== null && statusFilter.value !== undefined) {
          params.status = statusFilter.value
        }
        if (expireFilter.value !== null && expireFilter.value !== undefined) {
          params.expire_status = expireFilter.value
        }
        const response = await axios.get('/api/users', { params })
        if (response.data.success) {
          users.value = response.data.data
          totalUsers.value = response.data.total
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
        const response = await axios.post('/api/users', createUserForm.value)
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
        const response = await axios.put(`/api/users/${editUserForm.value.id}`, editUserForm.value)
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
        const response = await axios.put(`/api/users/${user.id}/status`, {
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
        const response = await axios.delete(`/api/users/${userId}`)
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
        const response = await axios.post('/api/users/sync')
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
        const response = await axios.post('/api/users/check-expire')
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
        const response = await axios.get('/api/emby/check-connection')
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

    // SSE连接对象
    const sseConnection = ref(null)

    // 执行CloudPan 189Share脚本
    const executeCloudPan189ShareScript = async () => {
      try {
        loading.value = true
        const response = await axios.post('/api/plugins/189share/execute')
        if (response.data.success) {
          ElMessage.success(response.data.message)
          // 执行后自动获取日志并建立SSE连接
          setTimeout(() => {
            fetchCloudPan189ShareLogs()
            establishSSEConnection()
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
        const response = await axios.get('/api/plugins/189share/logs')
        if (response.data.success) {
          cloudpan189shareLogs.value = response.data.logs
          console.log('获取到的日志内容:', response.data.logs)
          
          // 自动滚动到底部
          if (autoScrollEnabled.value) {
            setTimeout(() => {
              scrollToBottom()
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

    // 滚动到底部函数
    const scrollToBottom = () => {
      setTimeout(() => {
        if (scrollbarRef.value) {
          // 尝试不同的方式访问滚动容器
          const scrollContainer = scrollbarRef.value.wrap || scrollbarRef.value.$refs?.wrap || document.querySelector('.el-scrollbar__wrap')
          if (scrollContainer) {
            scrollContainer.scrollTop = scrollContainer.scrollHeight
            console.log('自动滚动到底部')
          } else {
            console.error('无法找到滚动容器')
          }
        } else {
          console.error('scrollbarRef未定义')
        }
      }, 50)
    }

    // 建立SSE连接
    const establishSSEConnection = () => {
      // 关闭现有的SSE连接
      if (sseConnection.value) {
        sseConnection.value.close()
        sseConnection.value = null
      }

      // 创建新的SSE连接
        const token = localStorage.getItem('token')
        console.log('建立SSE连接，token:', token)
        try {
          sseConnection.value = new EventSource(`/api/plugins/189share/logs/sse?token=${token}`)

        // 处理消息事件
        sseConnection.value.onmessage = (event) => {
          if (event.data && event.data !== '\n') {
            console.log('收到SSE消息:', event.data)
            // 添加新的日志内容
            cloudpan189shareLogs.value += '\n' + event.data
            
            // 自动滚动到底部
            if (autoScrollEnabled.value) {
              scrollToBottom()
            }
          }
        }

        // 处理打开事件
        sseConnection.value.onopen = (event) => {
          console.log('SSE连接已打开:', event)
        }

        // 处理错误事件
        sseConnection.value.onerror = (error) => {
          console.error('SSE连接错误:', error)
          console.error('SSE连接状态:', sseConnection.value?.readyState)
          // 关闭连接
          if (sseConnection.value) {
            sseConnection.value.close()
            sseConnection.value = null
          }
        }

        console.log('SSE连接已建立')
      } catch (error) {
        console.error('建立SSE连接时出错:', error)
      }
    }

    // 关闭SSE连接
    const closeSSEConnection = () => {
      console.log('尝试关闭SSE连接:', sseConnection.value)
      if (sseConnection.value) {
        try {
          sseConnection.value.close()
          sseConnection.value = null
          console.log('SSE连接已关闭')
        } catch (error) {
          console.error('关闭SSE连接时出错:', error)
        }
      } else {
        console.log('没有活跃的SSE连接')
      }
    }

    // 中断CloudPan 189Share脚本执行
    const stopCloudPan189ShareScript = async () => {
      try {
        loading.value = true
        const response = await axios.post('/api/plugins/189share/stop')
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

    // 日志管理相关方法
    const handleLogTypeChange = () => {
      if (logsForm.value.logType === 'plugin') {
        fetchPlugins()
      }
      // 重新建立SSE连接
      if (activeMenu.value === '5') {
        establishLogsSSEConnection()
      }
    }

    const fetchPlugins = async () => {
      try {
        const response = await axios.get('/api/logs/plugins')
        if (response.data.success) {
          availablePlugins.value = response.data.plugins
        }
      } catch (error) {
        console.error('获取插件列表失败:', error)
      }
    }

    const fetchLogs = async () => {
      try {
        loadingLogs.value = true
        let response
        if (logsForm.value.logType === 'all') {
          response = await axios.get('/api/logs/all')
        } else if (logsForm.value.logType === 'plugin' && logsForm.value.pluginName) {
          response = await axios.get(`/api/logs/plugin/${logsForm.value.pluginName}`)
        } else {
          ElMessage.warning('请选择插件')
          return
        }
        
        if (response.data.success) {
          logsContent.value = response.data.logs
          // 自动滚动到底部
          if (logsAutoScrollEnabled.value) {
            setTimeout(() => {
              scrollLogsToBottom()
            }, 100)
          }
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        const errorMessage = error.response?.data?.message || '获取日志失败'
        ElMessage.error(errorMessage)
        console.error(error)
      } finally {
        loadingLogs.value = false
      }
    }

    const scrollLogsToBottom = () => {
      setTimeout(() => {
        if (logsScrollbarRef.value) {
          // 尝试不同的方式访问滚动容器
          const scrollContainer = logsScrollbarRef.value.wrap || logsScrollbarRef.value.$refs?.wrap || document.querySelector('.el-scrollbar__wrap')
          if (scrollContainer) {
            scrollContainer.scrollTop = scrollContainer.scrollHeight
          }
        }
      }, 50)
    }

    // 日志管理SSE连接
    const logsSSEConnection = ref(null)

    const establishLogsSSEConnection = () => {
      // 关闭现有的SSE连接
      if (logsSSEConnection.value) {
        logsSSEConnection.value.close()
        logsSSEConnection.value = null
      }

      // 创建新的SSE连接
        const token = localStorage.getItem('token')
        console.log('建立日志SSE连接，token:', token)
        try {
          let sseUrl
          if (logsForm.value.logType === 'plugin' && logsForm.value.pluginName) {
            // 插件日志SSE
            sseUrl = `/api/logs/plugin/${logsForm.value.pluginName}/sse?token=${token}`
          } else {
            // 所有日志SSE
            sseUrl = `/api/logs/all/sse?token=${token}`
          }
          
          logsSSEConnection.value = new EventSource(sseUrl)

        // 处理消息事件
        logsSSEConnection.value.onmessage = (event) => {
          if (event.data && event.data !== '\n') {
            console.log('收到日志SSE消息:', event.data)
            // 添加新的日志内容
            logsContent.value += '\n' + event.data
            
            // 自动滚动到底部
            if (logsAutoScrollEnabled.value) {
              scrollLogsToBottom()
            }
          }
        }

        // 处理打开事件
        logsSSEConnection.value.onopen = (event) => {
          console.log('日志SSE连接已打开:', event)
        }

        // 处理错误事件
        logsSSEConnection.value.onerror = (error) => {
          console.error('日志SSE连接错误:', error)
          console.error('日志SSE连接状态:', logsSSEConnection.value?.readyState)
          // 关闭连接
          if (logsSSEConnection.value) {
            logsSSEConnection.value.close()
            logsSSEConnection.value = null
          }
        }

        console.log('日志SSE连接已建立:', sseUrl)
      } catch (error) {
        console.error('建立日志SSE连接时出错:', error)
      }
    }

    const closeLogsSSEConnection = () => {
      console.log('尝试关闭日志SSE连接:', logsSSEConnection.value)
      if (logsSSEConnection.value) {
        try {
          logsSSEConnection.value.close()
          logsSSEConnection.value = null
          console.log('日志SSE连接已关闭')
        } catch (error) {
          console.error('关闭日志SSE连接时出错:', error)
        }
      } else {
        console.log('没有活跃的日志SSE连接')
      }
    }

    // 清理日志
    const clearLogs = async () => {
      try {
        // 弹出确认对话框
        await ElMessageBox.confirm('确定要清理当前日志吗？此操作不可恢复。', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        // 关闭SSE连接
        closeLogsSSEConnection()

        // 根据日志类型调用相应的API
        let url
        if (logsForm.value.logType === 'plugin' && logsForm.value.pluginName) {
          url = `/api/logs/plugin/${logsForm.value.pluginName}/clear`
        } else {
          url = '/api/logs/all/clear'
        }

        // 调用清理日志API
        const response = await axios.post(url, {}, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })

        if (response.data.success) {
          ElMessage.success(response.data.message)
          // 清理成功后刷新日志
          setTimeout(() => {
            fetchLogs()
          }, 500)
          // 重新建立SSE连接
          setTimeout(() => {
            establishLogsSSEConnection()
          }, 1000)
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        if (error !== 'cancel') {
          const errorMessage = error.response?.data?.message || '清理日志失败'
          ElMessage.error(errorMessage)
          console.error('清理日志时出错:', error)
        }
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
      pageSize,
      customPageSize,
      totalUsers,
      actualPageSize,
      cloudpan189shareLogs,
      loadingCloudPanLogs,
      handleMenuSelect,
      toggleSidebar,
      handleCurrentChange,
      handlePageSizeChange,
      handleCustomPageSizeChange,
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
      handleLogout,
      // 日志管理相关
      logsForm,
      logsContent,
      loadingLogs,
      logsAutoScrollEnabled,
      logsScrollbarRef,
      availablePlugins,
      handleLogTypeChange,
      fetchLogs,
      fetchPlugins,
      // 日志管理SSE相关
      establishLogsSSEConnection,
      closeLogsSSEConnection,
      // 日志清理相关
      clearLogs
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

/* 分页控件样式 */
.pagination {
  margin-top: 5px;
}

.pagination-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 5px 0;
  margin-top: 5px;
  gap: 15px;
}

.page-size-selector {
  display: flex;
  align-items: center;
}

/* 调整分页控件的样式 */
:deep(.el-pagination) {
  margin: 0;
}

:deep(.el-pagination__sizes) {
  margin-right: 10px;
}

:deep(.el-pagination__jump) {
  margin-left: 10px;
}

:deep(.el-pagination__prev),
:deep(.el-pagination__next),
:deep(.el-pagination__page-btn) {
  border-radius: 4px;
  transition: all 0.3s ease;
}

:deep(.el-pagination__prev:hover),
:deep(.el-pagination__next:hover),
:deep(.el-pagination__page-btn:hover) {
  color: #409eff;
  border-color: #c6e2ff;
}

:deep(.el-pagination__page-btn.is-current) {
  background-color: #409eff;
  border-color: #409eff;
  color: #ffffff;
}

/* 调整输入框样式 */
:deep(.el-input-number) {
  width: 100px;
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  border-radius: 0;
}

:deep(.el-input-number__decrease) {
  border-right: none;
}

:deep(.el-input-number__increase) {
  border-left: none;
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
  padding: 16px 0;
}

.el-menu-item {
  color: rgba(255, 255, 255, 0.9);
  height: 48px;
  line-height: 48px;
  font-size: 14px;
  margin: 8px 12px !important;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
  font-weight: 500;
}

.el-menu-item .el-menu-tooltip__trigger {
  align-items: center;
  display: flex;
}

/* 收起状态下的tooltip触发器样式 */
.sidebar.collapsed .el-menu-item .el-menu-tooltip__trigger {
  justify-content: center;
}

.el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  transform: translateX(4px);
}

.el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 菜单图标样式 */
.el-menu-item .el-icon {
  font-size: 16px;
  margin-right: 12px;
  width: 20px;
  text-align: center;
}

/* 收起状态下的菜单样式 */
.sidebar.collapsed .el-menu-item {
  justify-content: center;
  padding: 0;
  width: calc(100% - 24px);
}

.sidebar.collapsed .el-menu-item .el-icon {
  margin-right: 0;
  font-size: 18px;
}

.sidebar.collapsed .el-menu-item .el-icon + span {
  display: none;
}

.sidebar.collapsed .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
}

.sidebar.collapsed .el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
  transform: none;
}

/* 页面头部样式 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background-color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  height: 64px;
  transition: all 0.3s ease;
  border-bottom: 1px solid #e8e8e8;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.sidebar-toggle {
  color: #666;
  font-size: 18px;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  color: #1989fa;
  box-shadow: 0 3px 12px rgba(25, 137, 250, 0.3);
  filter: brightness(1.05);
}

.header-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

/* 用户下拉菜单样式 */
.header-actions .el-dropdown {
  transition: all 0.3s ease;
}

.header-actions .el-dropdown:hover {
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.3);
  filter: brightness(1.05);
}

.header-actions .el-button {
  transition: all 0.3s ease;
}

.header-actions .el-button:hover {
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.3);
  filter: brightness(1.05);
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
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 128px);
  transition: all 0.3s ease;
}

/* 搜索卡片样式 */
.search-card {
  margin-bottom: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  overflow: hidden;
  background: white;
  transition: all 0.3s ease;
}

.search-card:hover {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  filter: brightness(1.02);
}

.search-form {
  width: 100%;
  padding: 20px;
}

/* 用户列表卡片样式 */
.user-list-card {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  overflow: hidden;
  background: white;
  transition: all 0.3s ease;
}

.user-list-card:hover {
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  filter: brightness(1.02);
}

/* 搜索表单样式 */
.search-form .el-form-item {
  margin-bottom: 16px;
}

.search-form .el-input {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.search-form .el-input:focus-within {
  box-shadow: 0 0 0 2px rgba(25, 137, 250, 0.2);
}

.search-form .el-select {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.search-form .el-select:focus-within {
  box-shadow: 0 0 0 2px rgba(25, 137, 250, 0.2);
}

.search-form .el-button {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.search-form .el-button:hover {
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.3);
  filter: brightness(1.05);
}

/* 表格样式 */
.el-table {
  width: 100% !important;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.el-table--striped .el-table__row--striped {
  background-color: #f8f9fa;
}

.el-table th {
  background-color: #f0f2f5;
  font-weight: 600;
  font-size: 14px;
  color: #404040;
  padding: 16px 12px;
  border-bottom: 1px solid #e8e8e8;
}

.el-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: #606060;
}

.el-table tr:hover > td {
  background-color: #f5f7fa !important;
}

.el-table__empty-block {
  min-height: 300px;
  background-color: #fafafa;
}

.el-table__empty-text {
  color: #909090;
  font-size: 14px;
}

/* 分页样式 */
.pagination {
  margin-top: 24px;
  padding: 16px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.el-pagination {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.el-pagination__item {
  border-radius: 6px;
  transition: all 0.3s ease;
}

.el-pagination__item:hover {
  color: #1989fa;
  border-color: #1989fa;
  box-shadow: 0 3px 12px rgba(25, 137, 250, 0.3);
  filter: brightness(1.05);
}

.el-pagination__item.is-current {
  background-color: #1989fa;
  border-color: #1989fa;
  color: white;
  font-weight: 600;
}

.el-pagination__button {
  border-radius: 6px;
  transition: all 0.3s ease;
}

.el-pagination__button:hover {
  color: #1989fa;
  border-color: #1989fa;
  box-shadow: 0 3px 12px rgba(25, 137, 250, 0.3);
  filter: brightness(1.05);
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.action-btn {
  margin: 0 !important;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-size: 12px;
  padding: 6px 12px;
}

.action-btn:hover {
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
  filter: brightness(1.05);
}

.action-btn.el-button--primary {
  background-color: #1989fa;
  border-color: #1989fa;
}

.action-btn.el-button--primary:hover {
  background-color: #1677ff;
  border-color: #1677ff;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
  filter: brightness(1.05);
}

.action-btn.el-button--warning {
  background-color: #faad14;
  border-color: #faad14;
}

.action-btn.el-button--warning:hover {
  background-color: #f7ba2a;
  border-color: #f7ba2a;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
  filter: brightness(1.05);
}

.action-btn.el-button--danger {
  background-color: #f5222d;
  border-color: #f5222d;
}

.action-btn.el-button--danger:hover {
  background-color: #ff4d4f;
  border-color: #ff4d4f;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
  filter: brightness(1.05);
}

.action-btn.el-button--success {
  background-color: #52c41a;
  border-color: #52c41a;
}

.action-btn.el-button--success:hover {
  background-color: #73d13d;
  border-color: #73d13d;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
  filter: brightness(1.05);
}

.action-btn.el-button--info {
  background-color: #1890ff;
  border-color: #1890ff;
}

.action-btn.el-button--info:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
  filter: brightness(1.05);
}

/* 居中内容样式 */
.center-content {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 128px);
  padding: 24px;
  background-color: #f5f7fa;
}

/* 全屏宽度内容样式 */
.full-width-content {
  width: 100%;
  min-height: calc(100vh - 128px);
  padding: 0;
  background-color: #f5f7fa;
  display: flex;
  justify-content: flex-start;
  align-items: stretch;
}

/* 卡片样式 */
.expire-card,
.connection-card {
  width: 100%;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

/* .expire-card:hover,
.connection-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
} */

.expire-content,
.connection-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 196px);
  gap: 24px;
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
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.3);
  filter: brightness(1.05);
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

/* .server-info-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
} */

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
@media screen and (max-width: 1024px) {
  .main-content {
    padding: 20px;
  }

  .page-header {
    padding: 0 20px;
  }
}

@media screen and (max-width: 768px) {
  /* 整体布局调整 */
  .app-container {
    flex-direction: column;
    min-height: 100vh;
  }

  /* 侧边栏调整为顶部导航 */
  .sidebar {
    width: 100% !important;
    height: auto;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .sidebar .logo {
    height: 56px;
    line-height: 56px;
    font-size: 16px;
  }

  /* 菜单调整为水平滚动 */
  .el-menu-vertical-demo {
    display: flex;
    height: auto;
    flex-direction: row;
    overflow-x: auto;
    padding: 8px 0;
    background-color: #1989fa;
  }

  .el-menu-vertical-demo::-webkit-scrollbar {
    height: 4px;
  }

  .el-menu-item {
    flex: 0 0 auto;
    text-align: center;
    height: 44px;
    line-height: 44px;
    white-space: nowrap;
    margin: 0 8px !important;
    border-radius: 6px;
    font-size: 13px;
  }

  .el-menu-item .el-icon {
    margin-right: 8px;
    font-size: 14px;
  }

  /* 页面头部调整 */
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    height: auto;
    min-height: 60px;
    width: 100%;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    width: 100%;
  }

  .sidebar-toggle {
    font-size: 16px;
    margin-right: 0;
  }

  /* 面包屑导航调整 */
  .el-breadcrumb {
    font-size: 13px;
  }

  /* 主内容区调整 */
  .main-content {
    padding: 16px;
    min-height: 400px;
    flex: 1;
    width: 100%;
  }

  /* 搜索表单调整 */
  .search-form {
    flex-direction: column;
    align-items: flex-start;
    padding: 16px;
  }

  .search-form .el-form-item {
    width: 100%;
    margin-bottom: 12px;
  }

  .search-form .el-input,
  .search-form .el-select {
    width: 100% !important;
  }

  /* 卡片调整 */
  .expire-card,
  .connection-card {
    width: 100%;
    margin: 0;
    max-width: none;
    height: auto;
    min-height: 300px;
  }

  .expire-content,
  .connection-content {
    padding: 40px 24px;
    min-height: 300px;
    gap: 24px;
  }

  .expire-content p,
  .connection-content p {
    font-size: 16px;
    padding: 0 16px;
  }

  /* 操作按钮调整 */
  .action-buttons {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }

  .action-btn {
    font-size: 11px;
    padding: 5px 10px;
    flex: 1;
    min-width: 70px;
    text-align: center;
  }

  /* 按钮调整 */
  .el-button {
    font-size: 13px;
    padding: 10px 18px;
  }

  /* 表格调整 */
  .el-table {
    font-size: 13px;
  }

  .el-table th,
  .el-table td {
    padding: 12px 8px;
    font-size: 13px;
  }

  /* 分页调整 */
  .pagination {
    margin-top: 16px;
    padding: 12px;
  }

  .el-pagination {
    flex-wrap: wrap;
    gap: 8px;
  }

  .el-pagination__item,
  .el-pagination__button {
    font-size: 12px;
    padding: 4px 10px;
  }

  /* 189Share管理页面调整 */
  .cloudpan189share-card {
    height: auto;
    min-height: 300px;
  }

  .cloudpan189share-content {
    padding: 20px;
    min-height: 300px;
  }

  .logs-content {
    padding: 16px;
    font-size: 13px;
  }

  .no-logs {
    padding: 32px;
  }

  /* 全屏宽度内容调整 */
  .full-width-content {
    min-height: 400px;
    flex: 1;
  }
}

/* 小屏幕手机适配 */
@media screen and (max-width: 480px) {
  .sidebar .logo {
    font-size: 14px;
  }

  .el-menu-item {
    font-size: 12px;
    padding: 0 12px;
  }

  .el-menu-item .el-icon {
    margin-right: 6px;
    font-size: 13px;
  }

  .main-content {
    padding: 12px;
    min-height: 400px;
    flex: 1;
  }

  .expire-content,
  .connection-content {
    padding: 32px 16px;
    min-height: 300px;
  }

  .expire-content p,
  .connection-content p {
    font-size: 15px;
    padding: 0 12px;
  }

  .action-buttons {
    flex-direction: column;
    align-items: stretch;
  }

  .action-btn {
    width: 100%;
  }

  /* 卡片调整 */
  .expire-card,
  .connection-card {
    min-height: 300px;
  }

  .cloudpan189share-card {
    min-height: 300px;
  }

  .cloudpan189share-content {
    min-height: 300px;
  }

  /* 全屏宽度内容调整 */
  .full-width-content {
    min-height: 400px;
    flex: 1;
  }
}

/* 横屏手机适配 */
@media screen and (max-height: 500px) and (orientation: landscape) {
  .sidebar {
    height: auto;
  }

  .el-menu-vertical-demo {
    padding: 4px 0;
  }

  .el-menu-item {
    height: 36px;
    line-height: 36px;
  }

  .main-content {
    min-height: 300px;
    flex: 1;
  }

  .expire-content,
  .connection-content {
    min-height: 250px;
    padding: 24px 16px;
  }

  /* 卡片调整 */
  .expire-card,
  .connection-card {
    min-height: 250px;
  }

  .cloudpan189share-card {
    min-height: 250px;
  }

  .cloudpan189share-content {
    min-height: 250px;
  }

  /* 全屏宽度内容调整 */
  .full-width-content {
    min-height: 300px;
    flex: 1;
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
  height: 100%;
}

/* .cloudpan189share-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
} */

.cloudpan189share-content {
  padding: 24px;
  min-height: calc(100vh - 196px);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.action-buttons {
  display: flex;
  gap: 12px;
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  filter: brightness(1.05);
}

.logs-card {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

/* .logs-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
} */

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