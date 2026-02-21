<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">Emby 管理系统</div>
      <el-menu
        default-active="1"
        class="el-menu-vertical-demo"
        mode="vertical"
        :default-openeds="['1']"
        unique-opened
        @select="handleMenuSelect"
      >
        <el-menu-item index="1">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="2">
          <el-icon><AlarmClock /></el-icon>
          <span>检查过期用户</span>
        </el-menu-item>
        <el-menu-item index="3">
          <el-icon><Connection /></el-icon>
          <span>检查 Emby 连接</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-main class="main-content">
      <!-- 页面标题和操作按钮 -->
      <div class="page-header">
        <h1>{{ pageTitle }}</h1>
        <div class="header-actions">
          <el-button type="primary" @click="openCreateUserDialog" v-if="activeMenu === '1'">
            <el-icon><Plus /></el-icon>
            创建用户
          </el-button>
          <el-button type="success" @click="syncUsers" v-if="activeMenu === '1'">
            <el-icon><Refresh /></el-icon>
            同步Emby用户
          </el-button>
        </div>
      </div>
      
      <!-- 搜索区域 -->
      <div class="search-section" v-if="activeMenu === '1'">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名"
          style="width: 300px; margin-right: 10px"
          clearable
        />
        <el-select
          v-model="statusFilter"
          placeholder="选择状态"
          style="width: 150px; margin-right: 10px"
          clearable
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        <el-select
          v-model="expireFilter"
          placeholder="选择过期状态"
          style="width: 150px; margin-right: 10px"
          clearable
        >
          <el-option label="未过期" :value="'active'" />
          <el-option label="已过期" :value="'expired'" />
        </el-select>
        <el-button type="info" @click="fetchUsers">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
      </div>

      <!-- 用户列表 -->
      <div v-if="activeMenu === '1'" class="user-list">
        <el-table :data="users" style="width: 100%" v-loading="loading">
          <el-table-column prop="emby_id" label="Emby ID" width="300" />
          <el-table-column prop="name" label="用户名" width="150" />
          <el-table-column prop="created_at" label="注册时间" width="200">
            <template #default="scope">
              {{ scope.row.created_at }}
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                {{ scope.row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="expire_date" label="过期时间" width="180">
            <template #default="scope">
              {{ scope.row.expire_date ? scope.row.expire_date : '永久' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="scope">
              <div class="action-buttons">
                <!-- 检查是否为受保护用户 -->
                <template v-if="['emby_tpl_user', 'huxt', 'test'].includes(scope.row.name)">
                  <el-button size="small" disabled class="action-btn">
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
                  <el-button size="small" type="danger" disabled class="action-btn">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
                <template v-else>
                  <el-button size="small" @click="openEditUserDialog(scope.row)" class="action-btn">
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
                  <el-button size="small" type="danger" @click="deleteUser(scope.row.id)" class="action-btn">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>



      <!-- 检查过期用户 -->
      <div v-if="activeMenu === '2'" class="expire-section">
        <el-card class="expire-card">
          <template #header>
            <div class="card-header">
              <span>检查过期用户</span>
            </div>
          </template>
          <div class="expire-content">
            <p>点击下方按钮检查并禁用过期用户</p>
            <el-button type="primary" @click="checkExpiredUsers">
              <el-icon><AlarmClock /></el-icon>
              检查过期
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 检查 Emby 连接 -->
      <div v-if="activeMenu === '3'" class="connection-section">
        <el-card class="connection-card">
          <template #header>
            <div class="card-header">
              <span>检查 Emby 连接</span>
            </div>
          </template>
          <div class="connection-content">
            <p>点击下方按钮检查与 Emby 服务器的连接状态</p>
            <el-button type="primary" @click="checkEmbyConnection">
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
              <el-card v-if="connectionStatus.connected && connectionStatus.server_info" class="server-info-card" style="margin-top: 20px">
                <template #header>
                  <div class="card-header">
                    <span>Emby 服务器信息</span>
                  </div>
                </template>
                <el-descriptions :column="1">
                  <el-descriptions-item label="服务器名称">{{ connectionStatus.server_info.name }}</el-descriptions-item>
                  <el-descriptions-item label="版本">{{ connectionStatus.server_info.version }}</el-descriptions-item>
                  <el-descriptions-item label="操作系统">{{ connectionStatus.server_info.operating_system }}</el-descriptions-item>
                </el-descriptions>
              </el-card>
            </div>
          </div>
        </el-card>
      </div>
    </el-main>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="createUserDialogVisible"
      title="创建用户"
      width="500px"
    >
      <el-form :model="createUserForm" :rules="createUserRules" ref="createUserFormRef">
        <el-form-item label="用户名" prop="name">
          <el-input v-model="createUserForm.name" placeholder="请输入用户名" />
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
    >
      <el-form :model="editUserForm" ref="editUserFormRef">
        <el-form-item label="用户名">
          <el-input v-model="editUserForm.name" disabled />
        </el-form-item>
        <el-form-item label="状态">
          <el-tag :type="editUserForm.is_active ? 'success' : 'danger'">
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


  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 配置 axios 基础路径
axios.defaults.baseURL = 'http://localhost:5000/api'

export default {
  name: 'App',
  setup() {
    // 响应式数据
    const activeMenu = ref('1')
    const users = ref([])
    const createUserDialogVisible = ref(false)
    const editUserDialogVisible = ref(false)
    const connectionStatus = ref(null)
    const searchQuery = ref('')
    const statusFilter = ref(null)
    const expireFilter = ref(null)
    const loading = ref(false)

    // 表单数据
    const createUserForm = ref({
      name: '',
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
      name: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
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
        default: return '用户管理'
      }
    })

    // 方法
    const handleMenuSelect = (key) => {
      activeMenu.value = key
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
        ElMessage.error('获取用户列表失败')
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    const openCreateUserDialog = () => {
      createUserForm.value = {
        name: '',
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
        ElMessage.error('创建用户失败')
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
        ElMessage.error('更新用户失败')
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
        ElMessage.error('操作失败')
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
          ElMessage.error('删除用户失败')
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
        ElMessage.error('同步失败')
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
        ElMessage.error('检查失败')
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
          ElMessage.error('检查连接状态失败')
        }
      } catch (error) {
        ElMessage.error('检查连接失败')
        console.error(error)
      } finally {
        loading.value = false
      }
    }

    // 生命周期
    onMounted(() => {
      fetchUsers()
    })

    return {
      activeMenu,
      users,
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
      handleMenuSelect,
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
      checkEmbyConnection
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
  height: 100vh;
  overflow: hidden;
  width: 100%;
  max-width: 100vw;
}

.sidebar {
  background-color: #303133;
  color: #fff;
  height: 100%;
  overflow: hidden;
  flex-shrink: 0;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 16px;
  font-weight: bold;
  background-color: #1890ff;
  color: white;
}

.el-menu-vertical-demo {
  height: calc(100% - 60px);
  border-right: none;
  background-color: #303133;
}

.el-menu-item {
  color: #fff;
  height: 50px;
  line-height: 50px;
  font-size: 14px;
  margin: 0 !important;
}

.el-menu-item:hover {
  background-color: #409eff !important;
  color: white !important;
}

.el-menu-item.is-active {
  background-color: #409eff !important;
  color: white !important;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.action-btn {
  margin: 0 !important;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f7fa;
  min-width: 0;
  max-width: none;
  width: calc(100vw - 200px);
}

/* 覆盖Element Plus默认样式 */
.el-container {
  width: 100% !important;
  max-width: none !important;
}

.el-main {
  padding: 20px !important;
  width: 100% !important;
  max-width: none !important;
  margin: 0 !important;
  min-width: 0 !important;
}

/* 调整用户列表容器 */
.user-list {
  background-color: #fff;
  border-radius: 4px;
  padding: 20px;
  overflow-x: auto;
  width: 100%;
  max-width: none;
  box-sizing: border-box;
}

/* 确保表格占满宽度 */
.el-table {
  width: 100% !important;
  max-width: none !important;
  box-sizing: border-box;
}

.el-table__header-wrapper,
.el-table__body-wrapper {
  width: 100% !important;
  max-width: none !important;
}

/* 搜索区域样式 */
.search-section {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  width: 100%;
  flex-wrap: wrap;
  gap: 10px;
}

/* 页面头部样式 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
  width: 100%;
}

.page-header h1 {
  font-size: 20px;
  color: #303133;
  margin: 0;
}

/* 同步、检查过期用户和检查连接区域样式 */
.sync-section,
.expire-section,
.connection-section {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 120px);
}

/* 卡片样式 */
.sync-card,
.expire-card,
.connection-card {
  width: 600px;
  text-align: center;
}

.sync-content,
.expire-content,
.connection-content {
  padding: 40px;
}

.sync-content p,
.expire-content p,
.connection-content p {
  margin-bottom: 30px;
  font-size: 16px;
  color: #606266;
}

.connection-result {
  margin-top: 30px;
}

.server-info-card {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .app-container {
    flex-direction: column;
    max-width: 100%;
    box-shadow: none;
  }

  .el-aside {
    width: 100% !important;
    height: auto;
  }

  .logo {
    height: 50px;
    line-height: 50px;
    font-size: 16px;
  }

  .el-menu-vertical-demo {
    display: flex;
    height: auto;
    flex-direction: row;
  }

  .el-menu-item {
    flex: 1;
    text-align: center;
    height: 45px;
    line-height: 45px;
  }

  .main-content {
    height: calc(100vh - 100px);
    padding: 10px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .action-buttons {
    flex-direction: column;
    align-items: flex-start;
  }

  .sync-card,
  .expire-card,
  .connection-card {
    width: 100%;
    margin: 0 10px;
  }

  .sync-content,
  .expire-content,
  .connection-content {
    padding: 20px;
  }
}
</style>