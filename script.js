// ============ API配置 ============
const API_BASE_URL = 'http://localhost:5000/api'

// API请求封装函数
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    })
    const data = await response.json()
    if (!data.success) {
      throw new Error(data.message || '请求失败')
    }
    return data.data
  } catch (error) {
    console.error('[v0] API请求失败:', error)
    throw error
  }
}

// ============ API接口调用函数 ============

// 接口1: 获取案例库选项
async function fetchCaseLibraryOptions() {
  console.log('[v0] 正在获取案例库选项...')
  return await apiRequest('/case-library-options')
}

// 接口2: 搜索历史用例
async function fetchSearchHistoryCases(caseLibrary, searchMethod, searchText) {
  console.log('[v0] 正在搜索历史用例...', { caseLibrary, searchMethod, searchText })
  return await apiRequest('/search-history-cases', {
    method: 'POST',
    body: JSON.stringify({
      caseLibrary,
      searchMethod,
      searchText
    })
  })
}

// 接口3: 获取预置步骤和组件
async function fetchPresetData() {
  console.log('[v0] 正在获取预置步骤和组件数据...')
  return await apiRequest('/preset-data')
}

// 接口4: 获取参数配置架构
async function fetchParamSchemas() {
  console.log('[v0] 正在获取参数配置架构...')
  return await apiRequest('/param-schemas')
}

// ============ 全局变量存储从后端获取的数据 ============
let caseLibraryOptions = []
let presetSteps = []
let presetComponents = []
let componentDefaultParams = {} // 组件默认参数，从后端获取
let currentSearchResults = [] // 存储当前搜索结果
let paramSchemas = {} // 参数配置架构，从后端获取

const defaultPresetSteps = [
  {
    id: "preset_1",
    name: "打开登录页面",
    description: "打开系统登录页面并等待加载完成",
    components: [
      { type: "api", name: "接口调用 - 获取登录页", params: { method: "GET", url: "/login" } },
      { type: "assert", name: "断言 - 页面加载完成", params: { type: "visible", selector: "#login-form" } },
    ],
  },
  {
    id: "preset_2",
    name: "输入用户名和密码",
    description: "在登录表单中输入用户凭证",
    components: [
      { type: "input", name: "输入框 - 用户名", params: { selector: "#username", value: "testuser" } },
      { type: "input", name: "输入框 - 密码", params: { selector: "#password", value: "password123" } },
    ],
  },
  {
    id: "preset_3",
    name: "点击登录按钮",
    description: "点击登录按钮提交表单",
    components: [{ type: "button", name: "按钮 - 登录", params: { selector: "#login-btn", action: "click" } }],
  },
  {
    id: "preset_4",
    name: "验证登录成功",
    description: "验证用户成功登录并跳转到首页",
    components: [
      { type: "assert", name: "断言 - URL跳转", params: { type: "url", expected: "/dashboard" } },
      { type: "assert", name: "断言 - 欢迎信息", params: { type: "text", selector: ".welcome", contains: "欢迎" } },
    ],
  },
  {
    id: "preset_5",
    name: "进入商品列表页",
    description: "导航到商品列表页面",
    components: [
      { type: "button", name: "按钮 - 商品导航", params: { selector: "#nav-products", action: "click" } },
      { type: "assert", name: "断言 - 页面标题", params: { type: "text", selector: "h1", expected: "商品列表" } },
    ],
  },
  {
    id: "preset_6",
    name: "输入搜索关键词",
    description: "在搜索框中输入搜索内容",
    components: [
      { type: "input", name: "输入框 - 搜索", params: { selector: "#search-input", value: "" } },
      { type: "button", name: "按钮 - 搜索", params: { selector: "#search-btn", action: "click" } },
    ],
  },
  {
    id: "preset_7",
    name: "选择商品规格",
    description: "选择商品的颜色、尺寸等规格",
    components: [
      { type: "select", name: "下拉选择 - 颜色", params: { selector: "#color-select", value: "" } },
      { type: "select", name: "下拉选择 - 尺寸", params: { selector: "#size-select", value: "" } },
    ],
  },
  {
    id: "preset_8",
    name: "点击加入购物车",
    description: "将商品添加到购物车",
    components: [
      { type: "button", name: "按钮 - 加入购物车", params: { selector: "#add-to-cart", action: "click" } },
      { type: "assert", name: "断言 - 添加成功提示", params: { type: "visible", selector: ".toast-success" } },
    ],
  },
  {
    id: "preset_9",
    name: "验证购物车数量",
    description: "验证购物车商品数量已更新",
    components: [
      { type: "assert", name: "断言 - 购物车数量", params: { type: "text", selector: ".cart-count", expected: "1" } },
    ],
  },
  {
    id: "preset_10",
    name: "提交订单",
    description: "确认订单信息并提交",
    components: [
      { type: "button", name: "按钮 - 提交订单", params: { selector: "#submit-order", action: "click" } },
      { type: "assert", name: "断言 - 订单成功", params: { type: "visible", selector: ".order-success" } },
    ],
  },
  {
    id: "preset_11",
    name: "用户已注册账号",
    description: "验证用户账号已存在于系统中",
    components: [{ type: "api", name: "接口调用 - 检查用户存在", params: { method: "GET", url: "/api/users/check" } }],
  },
  {
    id: "preset_12",
    name: "系统登录功能正常可用",
    description: "验证登录服务可正常访问",
    components: [{ type: "assert", name: "断言 - 登录页面可访问", params: { type: "status", expected: 200 } }],
  },
  {
    id: "preset_13",
    name: "商品库存充足",
    description: "验证商品有足够库存",
    components: [{ type: "api", name: "接口调用 - 检查库存", params: { method: "GET", url: "/api/products/stock" } }],
  },
  {
    id: "preset_14",
    name: "成功跳转到目标页面",
    description: "验证页面跳转成功",
    components: [{ type: "assert", name: "断言 - URL验证", params: { type: "url", expected: "" } }],
  },
  {
    id: "preset_15",
    name: "页面显示正确信息",
    description: "验证页面显示预期的内容",
    components: [{ type: "assert", name: "断言 - 文本验证", params: { type: "text", selector: "", contains: "" } }],
  },
]

// 临时兼容：保留一个默认的presetComponents用于页面初始化（将被API数据覆盖）
const defaultPresetComponents = [
  { id: "comp_phone", type: "phone", name: "号码配置", alias: "PhonesAssign", icon: "phone", description: "设置主被叫号码、呼叫区域和呼叫转移参数" },
  { id: "comp_variable", type: "variable", name: "设置变量", alias: "TableSetVar", icon: "variable", description: "创建并设置变量值、设置请求参数、预置测试数据" },
  { id: "comp_saveUserInfo", type: "saveUserInfo", name: "保存用户信息至变量", alias: "SaveUserInfo", icon: "save", description: "创建用户结束后，获取用户信息，保存至环境变量" },
  { id: "comp_moveForwardEfftime", type: "moveForwardEfftime", name: "时间前移", alias: "MoveForwardEfftime", icon: "clock-forward", description: "时间前移" },
  { id: "comp_delayTime", type: "delayTime", name: "时间延迟", alias: "DelayTime", icon: "clock-delay", description: "执行延迟时间" },
  { id: "comp_database", type: "database", name: "数据库查询", alias: "DataBaseQuery", icon: "database", description: "执行数据库查询数据的操作，查询某个表的某个字段值" },
  { id: "comp_api", type: "api", name: "Soap请求", alias: "SoapClient", icon: "globe", description: "发送Soap请求到指定接口，并校验接口返回数据" },
  { id: "comp_comment", type: "comment", name: "步骤注释", alias: "comment", icon: "message-square", description: "对自动化用例步骤进行注释" },
  { id: "comp_restful", type: "restful", name: "Rest请求", alias: "RestfulClient", icon: "send", description: "发送Rest请求，到接口，接收返回消息并对返回消息进行校验" },
  { id: "comp_shell", type: "shell", name: "Shell执行", alias: "ShellExec", icon: "terminal", description: "执行Shell命令" },
  { id: "comp_task", type: "task", name: "任务触发", alias: "TaskTrigger", icon: "play-circle", description: "触发定时任务执行" },
]

// ============ 历史用例搜索相关变量 ============

// 搜索方式选项（这个不需要改，保持前端固定）
const searchMethodOptions = [
  { value: "keyword", label: "按关键字" },
  { value: "semantic", label: "按语义" }
]

// 版本列表
const versionList = [
  { code: "CBS-SW25C00B888", name: "CBS系统版本 SW25C00B888" },
  { code: "CBS-SW25C00B777", name: "CBS系统版本 SW25C00B777" },
  { code: "CBS-SW25C00B666", name: "CBS系统版本 SW25C00B666" },
  { code: "BMP-V10.2", name: "BMP平台版本 V10.2" },
  { code: "BMP-V10.1", name: "BMP平台版本 V10.1" }
]

// Mock数据
const mockTestCases = [
  {
    id: "TC001",
    name: "用户登录功能测试",
    preconditions: [
      { 
        id: "p1", 
        name: "用户已注册", 
        expanded: false, 
        components: [
          { id: "pc1", type: "api", name: "接口调用 - 检查用户", params: { method: "GET", url: "/api/users/check" } }
        ] 
      }
    ],
    steps: [
      { 
        id: "s1", 
        name: "打开登录页", 
        expanded: true, 
        components: [
          { id: "c1", type: "api", name: "接口调用 - 获取登录页", params: { method: "GET", url: "/login" } }
        ] 
      },
      { 
        id: "s2", 
        name: "输入凭证", 
        expanded: false, 
        components: [
          { id: "c2", type: "input", name: "输入框 - 用户名", params: { selector: "#username", value: "testuser" } },
          { id: "c3", type: "input", name: "输入框 - 密码", params: { selector: "#password", value: "pass123" } }
        ] 
      }
    ],
    expectedResults: [
      { 
        id: "e1", 
        name: "登录成功", 
        expanded: false, 
        components: [
          { id: "ec1", type: "assert", name: "断言 - URL跳转", params: { type: "url", expected: "/dashboard" } }
        ] 
      }
    ]
  }
]

// 搜索结果mock数据
const mockSearchResults = [
  {
    id: "HTC001",
    name: "月度账单生成及计费验证",
    preconditions: [
      { 
        id: "hp1", 
        name: "初始化用户账户数据", 
        expanded: false, 
        components: [
          { id: "hpc1", type: "database", name: "数据库查询 - 检查账户状态", params: { dbUrl: "${Env.AdminDB}", sql: "select * from USER_ACCOUNT where status=1", timeout: "30" } },
          { id: "hpc2", type: "variable", name: "设置变量 - 账户参数", params: { vars: "My_AcctId=123456;My_BillCycle=202501" } }
        ] 
      }
    ],
    steps: [
      { 
        id: "hs1", 
        name: "执行账单计算任务", 
        expanded: true, 
        components: [
          { id: "hc1", type: "task", name: "任务触发 - 月度账单生成", params: { planType: "triggeringTaskPlan", planName: "Monthly_Bill_Generate", status: "f", timeout: "300" } },
          { id: "hc2", type: "delayTime", name: "时间延迟 - 等待任务完成", params: { delaytimes: "60" } }
        ] 
      },
      { 
        id: "hs2", 
        name: "验证账单数据准确性", 
        expanded: false, 
        components: [
          { id: "hc3", type: "database", name: "数据库查询 - 查询账单记录", params: { dbUrl: "${Env.DCDB204}", tableName: "DC_INVOICE_DETAIL", operation: "Select", conditions: "ACCT_ID|${My_AcctId}", timeout: "30" } }
        ] 
      }
    ],
    expectedResults: [
      { 
        id: "he1", 
        name: "账单生成成功且金额正确", 
        expanded: false, 
        components: [
          { id: "hec1", type: "database", name: "数据库查询 - 验证账单金额", params: { dbUrl: "${Env.DCDB204}", sql: "select count(*) from DC_INVOICE_DETAIL where ACCT_ID=${My_AcctId} and BILL_CYCLE='${My_BillCycle}'", checkAmount: "1" } }
        ] 
      }
    ]
  },
  {
    id: "HTC002",
    name: "用户套餐变更及生效验证",
    preconditions: [
      { 
        id: "hp2", 
        name: "创建测试用户", 
        expanded: false, 
        components: [
          { id: "hpc3", type: "phone", name: "号码配置 - 分配号码", params: { callingId: "Native_HD_C1A1_Onnet", callingVisit: "C1A1", calledId: "Native_HD_C1A1_Onnet", calledVisit: "C1A1" } },
          { id: "hpc4", type: "api", name: "SOAP接口调用 - 创建用户", params: { rTpl: "@\\soap\\CreateSubscriber.xml", url: "${Env.BMPAPP101.SoapUrl}", tenantId: "${My_tenantId}" } }
        ] 
      }
    ],
    steps: [
      { 
        id: "hs4", 
        name: "执行套餐变更操作", 
        expanded: false, 
        components: [
          { id: "hc4", type: "variable", name: "设置变量 - 变更套餐参数", params: { vars: "My_NewOfferingID=${Offer_NewPlan.ID};My_EffectiveDate=${G.now()}" } },
          { id: "hc5", type: "api", name: "SOAP接口调用 - 套餐变更", params: { rTpl: "@\\soap\\ModifyOffering.xml", url: "${Env.BMPAPP101.SoapUrl}", tenantId: "${My_tenantId}" } }
        ] 
      },
      { 
        id: "hs5", 
        name: "触发套餐生效处理", 
        expanded: false, 
        components: [
          { id: "hc6", type: "moveForwardEfftime", name: "时间前移 - 生效时间", params: { number: "${My_SubIdentity}", forwardhours: "24" } }
        ] 
      }
    ],
    expectedResults: [
      { 
        id: "he2", 
        name: "套餐变更成功并已生效", 
        expanded: false, 
        components: [
          { id: "hec2", type: "database", name: "数据库查询 - 验证套餐状态", params: { dbUrl: "${Env.AdminDB}", tableName: "SUBSCRIBER_OFFERING", operation: "Select", conditions: "SUB_ID|${calling.Sub.SUB_ID}", vars: "OFFERING_ID", timeout: "30" } },
          { id: "hec3", type: "shell", name: "Shell执行 - 验证日志", params: { url: "${Env.BMPAPP101.sshurl}", cmd: "grep 'ModifyOffering success' bmp_debug.log |wc -l", shellChecks: "1" } }
        ] 
      }
    ]
  },
  {
    id: "HTC003",
    name: "欠费停机及复机流程测试",
    preconditions: [
      { 
        id: "hp3", 
        name: "创建欠费用户", 
        expanded: false, 
        components: [
          { id: "hpc5", type: "phone", name: "号码配置 - 分配号码", params: { callingId: "Native_HD_C1A1_Onnet", callingVisit: "C1A1", calledId: "Native_HD_C1A1_Onnet", calledVisit: "C1A1" } },
          { id: "hpc6", type: "variable", name: "设置变量 - 开户参数", params: { vars: "My_PrimaryOfferingID=${Offer_ATP_Primary_POS.ID};My_Charge=1000000;My_tenantId=0" } },
          { id: "hpc7", type: "api", name: "SOAP接口调用 - 创建用户", params: { rTpl: "@\\soap\\CreateSubscriber.xml", url: "${Env.BMPAPP101.SoapUrl}", tenantId: "${My_tenantId}" } }
        ] 
      },
      { 
        id: "hp4", 
        name: "调整账户为欠费状态", 
        expanded: false, 
        components: [
          { id: "hpc8", type: "variable", name: "设置变量 - 欠费调整参数", params: { vars: "My_AdjOpType=1;My_AdjType=2;My_AdjAmt=5000000;My_AdjCurrencyID=1049" } },
          { id: "hpc9", type: "api", name: "SOAP接口调用 - 欠费调整", params: { rTpl: "@\\soap\\Adjustment.xml", url: "${Env.BMPAPP101.SoapUrl}", tenantId: "${My_tenantId}" } }
        ] 
      }
    ],
    steps: [
      { 
        id: "hs6", 
        name: "执行停机处理", 
        expanded: false, 
        components: [
          { id: "hc7", type: "task", name: "任务触发 - 欠费停机任务", params: { planType: "triggeringTaskPlan", planName: "Suspend_Debit_User", status: "f", tenantID: "${My_tenantId}", timeout: "120" } },
          { id: "hc8", type: "delayTime", name: "时间延迟 - 等待停机完成", params: { delaytimes: "30" } }
        ] 
      },
      { 
        id: "hs7", 
        name: "充值并执行复机", 
        expanded: false, 
        components: [
          { id: "hc9", type: "variable", name: "设置变量 - 充值参数", params: { vars: "My_PaymentAmt=10000000;My_PaymentMethod=1" } },
          { id: "hc10", type: "api", name: "SOAP接口调用 - 账户充值", params: { rTpl: "@\\soap\\Payment.xml", url: "${Env.BMPAPP101.SoapUrl}", tenantId: "${My_tenantId}" } },
          { id: "hc11", type: "task", name: "任务触发 - 复机任务", params: { planType: "triggeringTaskPlan", planName: "Resume_User_Service", status: "f", tenantID: "${My_tenantId}", timeout: "120" } }
        ] 
      }
    ],
    expectedResults: [
      { 
        id: "he3", 
        name: "用户成功复机且服务正常", 
        expanded: false, 
        components: [
          { id: "hec4", type: "database", name: "数据库查询 - 验证用户状态", params: { dbUrl: "${Env.AdminDB}", tableName: "SUBSCRIBER", operation: "Select", conditions: "SUB_ID|${calling.Sub.SUB_ID}", vars: "STATUS", timeout: "30" } },
          { id: "hec5", type: "comment", name: "步骤注释 - 验证完成", params: { content: "用户状态应为Active(1),余额大于0" } }
        ] 
      }
    ]
  }
]

// 已选择的历史用例
let selectedHistoryCases = []
// 临时选择的用例（在弹窗中）
let tempSelectedCases = []
// 当前编辑的历史用例
let historyCasesForEdit = []
let historyCasesBackup = null
let currentHistoryCaseIndex = 0
let isEditingHistoryCase = false
// 独立的用例模板数据（基于某个历史用例，但独立修改）
let caseTemplate = null
// 最终保存的用例模板
let savedCaseTemplate = null
// 保存的模板索引
let savedTemplateIndex = null

// 当前状态
let currentCaseIndex = 0
let testCases = []
let editingStepIndex = null
let editingComponentIndex = null
let editingSection = null // 'preconditions' | 'steps' | 'expectedResults'
let draggedElement = null
let draggedType = null
let draggedIndex = null
let draggedSection = null
let draggedStepIndex = null

let isGenerating = false
let generationComplete = false
let canDownload = false

let testCasesBackup = null

// 通知系统函数
function showNotification(message, type = "success", duration = 3000) {
  const container = elements.notificationContainer
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  
  const icons = {
    success: "✓",
    error: "✕",
    info: "ℹ",
    warning: "⚠",
  }
  
  notification.innerHTML = `
    <span class="notification-icon">${icons[type] || icons.success}</span>
    <span class="notification-text">${message}</span>
  `
  
  container.appendChild(notification)
  
  // 自动隐藏
  if (duration > 0) {
    setTimeout(() => {
      notification.classList.add("hide")
      setTimeout(() => {
        notification.remove()
      }, 300)
    }, duration)
  }
  
  return notification
}

// 确认对话框函数
function showConfirmDialog(message, title = "确认操作") {
  return new Promise((resolve) => {
    const overlay = document.getElementById("confirmDialog")
    const titleElement = document.getElementById("confirmDialogTitle")
    const messageElement = document.getElementById("confirmDialogMessage")
    const confirmBtn = document.getElementById("confirmDialogConfirm")
    const cancelBtn = document.getElementById("confirmDialogCancel")
    
    titleElement.textContent = title
    messageElement.textContent = message
    overlay.classList.add("show")
    
    const handleConfirm = () => {
      overlay.classList.remove("show")
      confirmBtn.removeEventListener("click", handleConfirm)
      cancelBtn.removeEventListener("click", handleCancel)
      resolve(true)
    }
    
    const handleCancel = () => {
      overlay.classList.remove("show")
      confirmBtn.removeEventListener("click", handleConfirm)
      cancelBtn.removeEventListener("click", handleCancel)
      resolve(false)
    }
    
    confirmBtn.addEventListener("click", handleConfirm)
    cancelBtn.addEventListener("click", handleCancel)
    
    // 点击背景关闭
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        handleCancel()
      }
    })
  })
}

let progressCounter = 0

let isFirstGeneration = true

// 新增用于存储选中的预设步骤
let selectedPresetStep = null
// 新增用于存储选中的预设组件
let selectedPresetComponent = null

// 历史用例相关变量已在上方声明

// DOM 元素
const elements = {}

// 参数配置相关变量
let currentParamConfig = {}
let currentComponentType = null
let allDefinedVariables = [] // 存储所有已定义的变量及其描述

// 初始化DOM元素引用
function initElements() {
  elements.notificationContainer = document.getElementById("notificationContainer")
  elements.historyCheckbox = document.getElementById("historyCheckbox")
  elements.awCheckbox = document.getElementById("awCheckbox")
  elements.historyUploadZone = document.getElementById("historyUploadZone")
  elements.caseUploadZone = document.getElementById("caseUploadZone")
  elements.awUploadZone = document.getElementById("awUploadZone")
  elements.historyFileInput = document.getElementById("historyFileInput")
  elements.caseFileInput = document.getElementById("caseFileInput")
  elements.awFileInput = document.getElementById("awFileInput")
  elements.historyFileDisplay = document.getElementById("historyFileDisplay")
  elements.caseFileDisplay = document.getElementById("caseFileDisplay")
  elements.awFileDisplay = document.getElementById("awFileDisplay")
  elements.historyFileName = document.getElementById("historyFileName")
  elements.caseFileName = document.getElementById("caseFileName")
  elements.awFileName = document.getElementById("awFileName")
  elements.removeHistoryFile = document.getElementById("removeHistoryFile")
  elements.removeCaseFile = document.getElementById("removeCaseFile")
  elements.removeAwFile = document.getElementById("removeAwFile")
  elements.chatMessages = document.getElementById("chatMessages")
  elements.chatInput = document.getElementById("chatInput")
  elements.sendBtn = document.getElementById("sendBtn")

  elements.chatActionButtons = document.getElementById("chatActionButtons")
  elements.chatInputArea = document.getElementById("chatInputArea")
  elements.generateBtn = document.getElementById("generateBtn")
  elements.modalOverlay = document.getElementById("modalOverlay")
  elements.closeModalBtn = document.getElementById("closeModalBtn")
  elements.continueGenerateBtn = document.getElementById("continueGenerateBtn")

  elements.cancelBtn = document.getElementById("cancelBtn")
  elements.saveBtn = document.getElementById("saveBtn")
  elements.caseList = document.getElementById("caseList")
  elements.caseDetailPanel = document.getElementById("caseDetailPanel")
  elements.detailTitle = document.getElementById("detailTitle")
  elements.detailId = document.getElementById("detailId")
  elements.stepsList = document.getElementById("stepsList")
  elements.addStepBtn = document.getElementById("addStepBtn")
  elements.preconditionList = document.getElementById("preconditionList")
  elements.addPreconditionBtn = document.getElementById("addPreconditionBtn")
  elements.expectedResultList = document.getElementById("expectedResultList")
  elements.addExpectedResultBtn = document.getElementById("addExpectedResultBtn")
  elements.stepEditOverlay = document.getElementById("stepEditOverlay")
  elements.closeStepEditBtn = document.getElementById("closeStepEditBtn")
  elements.stepNameInput = document.getElementById("stepNameInput")
  elements.stepDescInput = document.getElementById("stepDescInput")
  elements.cancelStepEditBtn = document.getElementById("cancelStepEditBtn")
  elements.saveStepBtn = document.getElementById("saveStepBtn")
  elements.stepEditTitle = document.getElementById("stepEditTitle")
  elements.componentEditOverlay = document.getElementById("componentEditOverlay")
  elements.closeComponentEditBtn = document.getElementById("closeComponentEditBtn")
  elements.componentTypeSelect = document.getElementById("componentTypeSelect")
  elements.componentNameInput = document.getElementById("componentNameInput")
  elements.componentParamsInput = document.getElementById("componentParamsInput")
  elements.cancelComponentEditBtn = document.getElementById("cancelComponentEditBtn")
  elements.saveComponentBtn = document.getElementById("saveComponentBtn")
  elements.componentEditTitle = document.getElementById("componentEditTitle")
  elements.confirmOverlay = document.getElementById("confirmOverlay")
  elements.closeConfirmBtn = document.getElementById("closeConfirmBtn")
  elements.confirmCancelBtn = document.getElementById("confirmCancelBtn")
  elements.confirmOkBtn = document.getElementById("confirmOkBtn")
  elements.confirmMessage = document.getElementById("confirmMessage")
  
  // 参数配置弹窗元素
  elements.paramConfigOverlay = document.getElementById("paramConfigOverlay")
  elements.closeParamConfigBtn = document.getElementById("closeParamConfigBtn")
  elements.cancelParamConfigBtn = document.getElementById("cancelParamConfigBtn")
  elements.saveParamConfigBtn = document.getElementById("saveParamConfigBtn")
  elements.paramConfigContainer = document.getElementById("paramConfigContainer")
  elements.openParamConfigBtn = document.getElementById("openParamConfigBtn")
  elements.paramSummary = document.getElementById("paramSummary")

  elements.stepNameSelectWrapper = document.getElementById("stepNameSelectWrapper")
  elements.stepNameDropdown = document.getElementById("stepNameDropdown")
  elements.componentNameSelectWrapper = document.getElementById("componentNameSelectWrapper")
  elements.componentNameDropdown = document.getElementById("componentNameDropdown")

  elements.tipsCard = document.getElementById("tipsCard")
  elements.tipsToggle = document.getElementById("tipsToggle")
  elements.tipsList = document.getElementById("tipsList")
}

// 初始化：加载后端数据
async function loadBackendData() {
  console.log('[v0] 开始加载后端数据...')
  try {
    // 加载预置步骤和组件数据
    const presetData = await fetchPresetData()
    presetSteps = presetData.steps || defaultPresetSteps
    presetComponents = presetData.components || defaultPresetComponents
    componentDefaultParams = presetData.componentDefaultParams || {}
    console.log('[v0] 预置数据加载成功:', { 
      steps: presetSteps.length, 
      components: presetComponents.length,
      componentParams: Object.keys(componentDefaultParams).length 
    })
    
    // 案例库选项会在用户打开筛选面板时按需加载
  } catch (error) {
    console.error('[v0] 加载后端数据失败，使用默认数据:', error)
    // 使用默认数据
    presetSteps = defaultPresetSteps
    presetComponents = defaultPresetComponents
    componentDefaultParams = {} // 如果加载失败，使用空对象
  }
}

// 初始化
function init() {
  initElements()
  
  // 加载后端数据
  loadBackendData()
  
  if (elements.tipsToggle) {
    elements.tipsToggle.addEventListener("click", toggleTips)
  }
  
  // 复选框事件 - historyCheckbox事件已移到bindHistorySearchEvents中
  
  elements.awCheckbox.addEventListener("change", () => {
    elements.awUploadZone.style.display = elements.awCheckbox.checked ? "block" : "none"
  })

  // 上传区域
  setupUploadZone(elements.caseUploadZone, elements.caseFileInput, elements.caseFileDisplay, elements.caseFileName)
  setupUploadZone(elements.awUploadZone, elements.awFileInput, elements.awFileDisplay, elements.awFileName)

  // 移除文件
  elements.removeCaseFile.addEventListener("click", () => removeFile("case"))
  elements.removeAwFile.addEventListener("click", () => removeFile("aw"))

  elements.generateBtn.addEventListener("click", startGeneration)

  // 聊天
  elements.sendBtn.addEventListener("click", sendMessage)
  elements.chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage()
  })

  // 模态框
  elements.closeModalBtn.addEventListener("click", cancelAndCloseModal)
  elements.cancelBtn.addEventListener("click", cancelAndCloseModal)
  elements.saveBtn.addEventListener("click", saveAndCloseModal)
  elements.modalOverlay.addEventListener("click", (e) => {
    if (e.target === elements.modalOverlay) cancelAndCloseModal()
  })

  elements.continueGenerateBtn.addEventListener("click", showContinueConfirm)

  // 添加按钮事件
  elements.addPreconditionBtn.addEventListener("click", () => openStepEdit(null, "preconditions"))
  elements.addStepBtn.addEventListener("click", () => openStepEdit(null, "steps"))
  elements.addExpectedResultBtn.addEventListener("click", () => openStepEdit(null, "expectedResults"))

  // 步骤编辑弹窗
  elements.closeStepEditBtn.addEventListener("click", closeStepEdit)
  elements.cancelStepEditBtn.addEventListener("click", closeStepEdit)
  // 使用onclick而不是addEventListener，以便后续可以覆盖
  elements.saveStepBtn.onclick = saveStep

  // 组件编辑弹窗
  elements.closeComponentEditBtn.addEventListener("click", closeComponentEdit)
  elements.cancelComponentEditBtn.addEventListener("click", closeComponentEdit)
  // 使用onclick而不是addEventListener，以便后续可以覆盖
  elements.saveComponentBtn.onclick = saveComponent
  // elements.componentTypeSelect.addEventListener("change", loadComponentDefaultParams)

  if (typeof initSearchableSelect !== 'undefined') {
    initSearchableSelect(elements.stepNameInput, elements.stepNameDropdown, presetSteps, renderStepOption, onStepSelected)

    initSearchableSelect(
      elements.componentTypeSelect,
      elements.componentNameDropdown,
      presetComponents,
      renderComponentOption,
      onComponentSelected,
    )
  }

  // 确认弹窗
  elements.closeConfirmBtn.addEventListener("click", closeConfirm)
  elements.confirmCancelBtn.addEventListener("click", closeConfirm)
  elements.confirmOkBtn.addEventListener("click", confirmContinueGenerate)
  
  // 参数配置弹窗
  elements.openParamConfigBtn.addEventListener("click", openParamConfig)
  elements.closeParamConfigBtn.addEventListener("click", closeParamConfig)
  elements.cancelParamConfigBtn.addEventListener("click", closeParamConfig)
  elements.saveParamConfigBtn.addEventListener("click", saveParamConfig)
  elements.paramConfigOverlay.addEventListener("click", (e) => {
    if (e.target === elements.paramConfigOverlay) closeParamConfig()
  })
}

// ============ 参数配置����能 ============

// 递归收集JSON树中的saveAs变量
function collectSaveAsVariables(obj, componentName, variables, parentPath = '') {
  if (!obj || typeof obj !== 'object') return
  
  Object.keys(obj).forEach(key => {
    const node = obj[key]
    const currentPath = parentPath ? `${parentPath}.${key}` : key
    if (node && typeof node === 'object') {
      if (node.type && node.saveAs && node.saveAs.trim()) {
        // 这是一个叶子节点，有saveAs属性且值不为空
        // 判断是SOAP还是REST组件
        const isApiComponent = componentName.includes('SOAP') || componentName.includes('Soap') || componentName.includes('接口')
        const isRestComponent = componentName.includes('REST') || componentName.includes('Rest')
        const typePrefix = isApiComponent ? 'SOAP请求' : (isRestComponent ? 'REST请求' : '接口')
        
        variables.push({
          name: node.saveAs,
          description: `${typePrefix}响应字段 ${currentPath}`
        })
      } else if (!node.type) {
        // 这是一个嵌套对象，递归处理
        collectSaveAsVariables(node, componentName, variables, currentPath)
      }
    }
  })
}

// 收集当前用例中所有已定义的变量
function collectAllVariables() {
  const variables = []
  let currentCase = testCases[currentCaseIndex]
  
  // 如果testCases为空，尝试从历史用例编辑模式或模板中获取
  if (!currentCase && typeof isViewingTemplate !== 'undefined') {
    if (isViewingTemplate && typeof caseTemplate !== 'undefined') {
      currentCase = caseTemplate
    } else if (typeof historyCasesForEdit !== 'undefined' && typeof currentEditCaseIndex !== 'undefined') {
      currentCase = historyCasesForEdit[currentEditCaseIndex]
    }
  }
  
  if (!currentCase) {
    return variables
  }
  
  // 收集预置条件中的变量
  currentCase.preconditions?.forEach(precondition => {
    precondition.components?.forEach(component => {
      if (component.type === 'variable' && component.params?.vars) {
        const vars = parseVariables(component.params.vars)
        const descriptions = component.params.varDescriptions ? component.params.varDescriptions.split(';') : []
        const descMap = {}
        descriptions.forEach(desc => {
          const [name, description] = desc.split(':')
          if (name && description) {
            descMap[name.trim()] = description.trim()
          }
        })
        vars.forEach(v => {
          if (v.name) {
            variables.push({
              name: v.name,
              description: descMap[v.name] || v.description || ''
            })
          }
        })
      }
      
      // 也收集预置条件中API/REST响应的saveAs变量
      if ((component.type === 'api' || component.type === 'restful') && component.params?.rRsp) {
        collectSaveAsVariables(component.params.rRsp, component.name || component.type, variables)
      }
    })
  })
  
  // 收集测试步骤中的变量
  currentCase.steps?.forEach(step => {
    step.components?.forEach(component => {
      if (component.type === 'variable' && component.params?.vars) {
        const vars = parseVariables(component.params.vars)
        const descriptions = component.params.varDescriptions ? component.params.varDescriptions.split(';') : []
        const descMap = {}
        descriptions.forEach(desc => {
          const [name, description] = desc.split(':')
          if (name && description) {
            descMap[name.trim()] = description.trim()
          }
        })
        vars.forEach(v => {
          if (v.name) {
            variables.push({
              name: v.name,
              description: descMap[v.name] || v.description || ''
            })
          }
        })
      }
      
      // 收集API/REST响应验证中的saveAs变量
      if ((component.type === 'api' || component.type === 'restful') && component.params?.rRsp) {
        collectSaveAsVariables(component.params.rRsp, component.name || component.type, variables)
      }
    })
  })
  
  // 收集预期结果中的变量（包括saveAs）
  currentCase.expectedResults?.forEach(result => {
    result.components?.forEach(component => {
      if ((component.type === 'api' || component.type === 'restful') && component.params?.rRsp) {
        collectSaveAsVariables(component.params.rRsp, component.name || component.type, variables)
      }
    })
  })
  
  // 去重
  const uniqueVars = []
  const seen = new Set()
  variables.forEach(v => {
    if (!seen.has(v.name)) {
      seen.add(v.name)
      uniqueVars.push(v)
    }
  })
  
  return uniqueVars
}

function openParamConfig() {
  // 更新全局变量列表
  allDefinedVariables = collectAllVariables()
  
  // 获取当前组件类型
  let componentType = null
  if (selectedPresetComponent) {
    componentType = selectedPresetComponent.type
  } else {
    const componentName = elements.componentTypeSelect.value
    const preset = presetComponents.find(p => p.name === componentName)
    if (preset) {
      componentType = preset.type
    }
  }
  
  currentComponentType = componentType
  
  // 获取当前参数值
  try {
    const currentValue = elements.componentParamsInput.value
    currentParamConfig = currentValue ? JSON.parse(currentValue) : {}
  } catch (e) {
    currentParamConfig = {}
  }
  
  // 如果没有参数配置，尝试从默认参数加载
  if (Object.keys(currentParamConfig).length === 0 && componentType && componentDefaultParams[componentType]) {
    currentParamConfig = JSON.parse(JSON.stringify(componentDefaultParams[componentType]))
  }
  
  // 生成表单
  generateParamForm(componentType, currentParamConfig)
  
  elements.paramConfigOverlay.classList.add("active")
}

function closeParamConfig() {
  console.log('[v0] 关闭参数配置弹窗')
  elements.paramConfigOverlay.classList.remove("active")
  currentParamConfig = {}
  currentComponentType = null
}

function saveParamConfig() {
  console.log('[v0] 保存参数配置')
  
  // 收集表单数据
  const formData = collectParamFormData()
  console.log('[v0] 收集到的参数:', formData)
  
  // 更新隐藏的输入框
  elements.componentParamsInput.value = JSON.stringify(formData, null, 2)
  
  // 更新参数摘要显示
  updateParamSummary(formData)
  
  closeParamConfig()
  showNotification("参数配置已保存", "success", 2000)
}

function generateParamForm(componentType, params) {
  console.log('[v0] 生成参数表单:', componentType, params)
  
  const container = elements.paramConfigContainer
  container.innerHTML = ''
  
  if (!componentType) {
  container.innerHTML = '<p style="text-align:center;color:#7f8c8d;padding:40px;">请先选择组件类型</p>'
  return
  }
  
  // 根据组件类型生成不同的表单
  const paramSchema = getParamSchema(componentType)
  
  if (!paramSchema || paramSchema.length === 0) {
  container.innerHTML = '<p style="text-align:center;color:#7f8c8d;padding:40px;">该组件无需配置参数</p>'
  return
  }
  
  // 检查是否有json-tree类型字段，如果有则添加全局"显示全部字段"开关
  const hasJsonTree = paramSchema.some(f => f.type === 'json-tree')
  if (hasJsonTree) {
    container.insertAdjacentHTML('beforeend', `
      <div class="param-global-toggle">
        <label class="json-tree-toggle-label json-tree-toggle-global" title="切换显示全部字段或仅显示已填写的字段">
          <input type="checkbox" class="json-tree-show-all-fields-global" checked>
          <span class="json-tree-toggle-text">显示全部字段</span>
        </label>
      </div>
    `)
  }
  
  paramSchema.forEach(field => {
  const fieldHtml = generateParamField(field, params[field.name] || '')
  container.insertAdjacentHTML('beforeend', fieldHtml)
  })
  
  // 绑定combo box事件
  bindComboBoxEvents()
  
  // 特殊处理：变量类型需要动态添加功能
  if (componentType === 'variable') {
    bindVariableListEvents()
  }
  
  // 绑定autocomplete事件
  bindAutocompleteEvents()
  
  // 绑定JSON树事件
  bindJsonTreeEvents()
  
  // 绑定全局显示切换
  bindGlobalShowAllFieldsToggle()
}



function getParamSchema(componentType) {
  // 从缓存的 paramSchemas 中获取架构
  return paramSchemas[componentType] || []
}

function generateParamField(field, value) {
  const requiredClass = field.required ? 'required' : ''
  const requiredMark = field.required ? ' *' : ''
  
  if (field.type === 'input') {
    return `
      <div class="param-field">
        <label class="param-field-label ${requiredClass}">${field.label}${requiredMark}</label>
        <div class="param-autocomplete-wrapper">
          <input type="text" class="param-field-input" data-name="${field.name}" value="${value || ''}" placeholder="${field.placeholder || ''}" data-autocomplete>
          <div class="param-autocomplete-dropdown"></div>
        </div>
        ${field.hint ? `<span class="param-field-hint">${field.hint}</span>` : ''}
      </div>
    `
  } else if (field.type === 'template-select') {
    // 模板文件下拉选择
    const options = (field.options || []).map(opt => {
      const selected = value === opt.value ? 'selected' : ''
      return `<option value="${opt.value}" ${selected}>${opt.label} (${opt.value})</option>`
    }).join('')
    return `
      <div class="param-field">
        <label class="param-field-label ${requiredClass}">${field.label}${requiredMark}</label>
        <div class="param-template-select-wrapper">
          <select class="param-template-select" data-name="${field.name}">
            <option value="">请选择模板文件...</option>
            ${options}
          </select>
          <input type="text" class="param-template-custom" data-name="${field.name}-custom" value="${value && !field.options?.find(o => o.value === value) ? value : ''}" placeholder="或输入自定义模板路径">
        </div>
        ${field.hint ? `<span class="param-field-hint">${field.hint}</span>` : ''}
      </div>
    `
  } else if (field.type === 'combo') {
    // Combo box: 可以从下拉选择，也可以自由输入
    const options = (field.options || []).map(opt => {
      return `<div class="param-combo-option" data-value="${opt}">${opt}</div>`
    }).join('')
    return `
  <div class="param-field">
  <label class="param-field-label ${requiredClass}">${field.label}${requiredMark}</label>
  <div class="param-combo-wrapper" data-combo data-name="${field.name}">
  <input type="text" class="param-combo-input" value="${value || ''}" placeholder="${field.placeholder || '请选择或输入'}">
  <button type="button" class="param-combo-toggle">
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M6 9l6 6 6-6"/>
  </svg>
  </button>
      <div class="param-combo-dropdown">
        ${options || '<div class="param-combo-no-options" style="padding: 12px; color: #95a5a6; text-align: center;">无可选项</div>'}
      </div>
  </div>
  ${field.hint ? `<span class="param-field-hint">${field.hint}</span>` : ''}
  </div>
  `
  } else if (field.type === 'textarea') {
    return `
      <div class="param-field">
        <label class="param-field-label ${requiredClass}">${field.label}${requiredMark}</label>
        <div class="param-autocomplete-wrapper">
          <textarea class="param-field-textarea" data-name="${field.name}" placeholder="${field.placeholder || ''}" data-autocomplete>${value || ''}</textarea>
          <div class="param-autocomplete-dropdown"></div>
        </div>
        ${field.hint ? `<span class="param-field-hint">${field.hint}</span>` : ''}
      </div>
    `
  } else if (field.type === 'variable-list') {
    // 解析 vars 参数，格式为 "My_Var1=value1;My_Var2=value2"
    const variables = parseVariables(value)
    const variablesHtml = variables.map((v, idx) => `
      <div class="param-variable-item">
        <div class="param-variable-inputs">
          <input type="text" placeholder="变量名 (My_)" value="${v.name}" data-var-name>
          <input type="text" placeholder="变量值" value="${v.value}" data-var-value>
          <input type="text" placeholder="变量描述" value="${v.description || ''}" data-var-desc>
        </div>
        <button type="button" class="param-variable-remove" data-remove-var>×</button>
      </div>
    `).join('')
    
    return `
      <div class="param-field">
        <label class="param-field-label ${requiredClass}">${field.label}${requiredMark}</label>
        <div class="param-variables-list" data-variables-list>
          ${variablesHtml || '<div class="param-variable-item"><div class="param-variable-inputs"><input type="text" placeholder="变量名 (My_)" data-var-name><input type="text" placeholder="变量值" data-var-value><input type="text" placeholder="变量描述" data-var-desc></div><button type="button" class="param-variable-remove" data-remove-var>×</button></div>'}
        </div>
        <button type="button" class="param-add-variable-btn" data-add-variable>
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>添加变量</span>
        </button>
        <span class="param-field-hint">变量名自动添加 "My_" 前缀，多个变量用分号分隔</span>
      </div>
    `
  } else if (field.type === 'json-tree') {
    // JSON树形结构编辑器
    const jsonData = value || field.defaultValue || {}
    const isResponse = field.isResponse || false
    const treeHtml = generateJsonTree(jsonData, field.name, 0, '', isResponse)
    
  return `
  <div class="param-field param-field-json-tree" data-is-response="${isResponse}" data-field-name="${field.name}">
  <div class="param-field-header">
  <label class="param-field-label ${requiredClass}">${field.label}${requiredMark}</label>
  <div class="json-tree-actions">
  <button type="button" class="json-tree-btn json-tree-expand-all" data-tree-name="${field.name}" title="展开全部">
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <polyline points="15 3 21 3 21 9"></polyline>
  <polyline points="9 21 3 21 3 15"></polyline>
  <line x1="21" y1="3" x2="14" y2="10"></line>
  <line x1="3" y1="21" x2="10" y2="14"></line>
  </svg>
  </button>
  <button type="button" class="json-tree-btn json-tree-collapse-all" data-tree-name="${field.name}" title="折叠全部">
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <polyline points="4 14 10 14 10 20"></polyline>
  <polyline points="20 10 14 10 14 4"></polyline>
  <line x1="14" y1="10" x2="21" y2="3"></line>
  <line x1="3" y1="21" x2="10" y2="14"></line>
  </svg>
  </button>
  </div>
  </div>
  <div class="json-tree-container" data-json-tree="${field.name}" data-is-response="${isResponse}">
  ${treeHtml}
  </div>
  <input type="hidden" data-name="${field.name}" data-json-tree-value value='${JSON.stringify(jsonData)}'>
  ${field.hint ? `<span class="param-field-hint">${field.hint}</span>` : ''}
  </div>
  `
  }
  
  return ''
}

function parseVariables(varsString) {
  if (!varsString) return []
  
  const pairs = varsString.split(';').filter(p => p.trim())
  return pairs.map(pair => {
    const [name, value] = pair.split('=').map(s => s.trim())
    return { name: name || '', value: value || '', description: '' }
  })
}

// ============ JSON树形结构编辑器函数 ============

function generateJsonTree(data, treeName, level, parentPath = '', isResponse = false) {
  if (!data || typeof data !== 'object') {
    return '<div class="json-tree-empty">无数据</div>'
  }
  
  let html = ''
  const keys = Object.keys(data)
  
  keys.forEach(key => {
    const node = data[key]
    const currentPath = parentPath ? `${parentPath}.${key}` : key
    const isExpandable = node && typeof node === 'object' && !node.type
    const isLeaf = node && node.type
    const isDefault = node && node.isDefault
    
    if (isExpandable) {
      // 可展开的节点（嵌套对象）
      html += `
        <div class="json-tree-node json-tree-branch" data-path="${currentPath}" data-level="${level}">
          <div class="json-tree-node-header" data-toggle-node>
            <span class="json-tree-toggle">
              <svg class="json-tree-arrow" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </span>
            <span class="json-tree-key">${key}</span>
            <span class="json-tree-type-badge">object</span>
            <span class="json-tree-count">${Object.keys(node).length} 项</span>
          </div>
          <div class="json-tree-children" style="display: block;">
            ${generateJsonTree(node, treeName, level + 1, currentPath, isResponse)}
          </div>
        </div>
      `
    } else if (isLeaf) {
      // 叶子节点（带类型的值）
      const inputHtml = generateJsonTreeInput(node, currentPath, treeName)
      const validationHtml = isResponse ? generateValidationSelector(node, currentPath, treeName) : ''
      const saveAsHtml = isResponse ? generateSaveAsInput(node, currentPath, treeName) : ''
      
      html += `
        <div class="json-tree-node json-tree-leaf ${isDefault ? 'is-default-value' : ''}" data-path="${currentPath}" data-level="${level}" data-is-default="${isDefault || false}">
          <div class="json-tree-leaf-content">
            <span class="json-tree-key">${key}</span>
            <span class="json-tree-type-badge json-tree-type-${node.type}">${node.type}</span>
            ${inputHtml}
            ${validationHtml}
            ${saveAsHtml}
          </div>
        </div>
      `
    }
  })
  
  return html || '<div class="json-tree-empty">无字段</div>'
}

function generateValidationSelector(node, path, treeName) {
  const validation = node.validation || 'noCare'
  const validationOptions = [
    { value: 'noCare', label: '不校验', icon: '○' },
    { value: 'notEmpty', label: '非空', icon: '≠∅' },
    { value: 'equals', label: '等于', icon: '=' },
    { value: 'contains', label: '包含', icon: '∋' },
    { value: 'regex', label: '正则', icon: '.*' }
  ]
  
  const optionsHtml = validationOptions.map(opt => `
    <button type="button" class="validation-option ${validation === opt.value ? 'active' : ''}" 
            data-validation="${opt.value}" data-path="${path}" data-tree="${treeName}" title="${opt.label}">
      ${opt.icon}
    </button>
  `).join('')
  
  return `
    <div class="json-tree-validation-selector" data-current="${validation}">
      ${optionsHtml}
    </div>
  `
}

function generateSaveAsInput(node, path, treeName) {
  const saveAs = node.saveAs || ''
  return `
    <div class="json-tree-saveas-wrapper">
      <span class="saveas-arrow">→</span>
      <input type="text" class="json-tree-saveas-input" data-path="${path}" data-tree="${treeName}" 
             value="${saveAs}" placeholder="变量名(可选)" title="保存响应值到变量">
    </div>
  `
}

function generateJsonTreeInput(node, path, treeName) {
  const value = node.value || ''
  const nodeType = node.type || 'string'
  
  switch (nodeType) {
  case 'string':
  return `
  <div class="json-tree-input-wrapper">
    <input type="text" class="json-tree-input json-tree-input-string" data-path="${path}" data-tree="${treeName}" value="${escapeHtml(value)}" placeholder="字符串值" data-autocomplete>
    <div class="json-tree-autocomplete-dropdown"></div>
  </div>`
  case 'number':
  return `<input type="number" class="json-tree-input json-tree-input-number" data-path="${path}" data-tree="${treeName}" value="${value}" placeholder="数字值">`
  case 'boolean':
  return `
  <select class="json-tree-input json-tree-input-boolean" data-path="${path}" data-tree="${treeName}">
  <option value="true" ${value === true || value === 'true' ? 'selected' : ''}>true</option>
  <option value="false" ${value === false || value === 'false' ? 'selected' : ''}>false</option>
  </select>
  `
  case 'date':
  return `
  <div class="json-tree-input-wrapper">
    <input type="text" class="json-tree-input json-tree-input-date" data-path="${path}" data-tree="${treeName}" value="${escapeHtml(value)}" placeholder="日期值 或 \${G.today()}" data-autocomplete>
    <div class="json-tree-autocomplete-dropdown"></div>
  </div>`
  default:
  return `
  <div class="json-tree-input-wrapper">
    <input type="text" class="json-tree-input" data-path="${path}" data-tree="${treeName}" value="${escapeHtml(value)}" data-autocomplete>
    <div class="json-tree-autocomplete-dropdown"></div>
  </div>`
  }
}

function escapeHtml(str) {
  if (typeof str !== 'string') return str
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function getValidationIcon(validation) {
  const icons = {
    'equals': '=',
    'contains': '∋',
    'notEmpty': '≠∅',
    'regex': '.*',
    'gt': '>',
    'lt': '<',
    'gte': '≥',
    'lte': '≤'
  }
  return `<span class="validation-icon">${icons[validation] || '✓'}</span>`
}

function bindJsonTreeEvents() {
  const trees = elements.paramConfigContainer.querySelectorAll('[data-json-tree]')
  
  trees.forEach(tree => {
    const treeName = tree.dataset.jsonTree
    
    // 展开/折叠节点
    tree.querySelectorAll('[data-toggle-node]').forEach(header => {
      header.addEventListener('click', (e) => {
        e.stopPropagation()
        const node = header.closest('.json-tree-branch')
        const children = node.querySelector('.json-tree-children')
        const arrow = header.querySelector('.json-tree-arrow')
        
        if (children.style.display === 'none') {
          children.style.display = 'block'
          arrow.style.transform = 'rotate(90deg)'
          node.classList.add('expanded')
        } else {
          children.style.display = 'none'
          arrow.style.transform = 'rotate(0deg)'
          node.classList.remove('expanded')
        }
      })
    })
    
    // 输入值变化时更新隐藏字段
    tree.querySelectorAll('.json-tree-input').forEach(input => {
      input.addEventListener('change', () => {
        updateJsonTreeValue(treeName)
      })
      input.addEventListener('input', () => {
        updateJsonTreeValue(treeName)
      })
    })
  })
  
  // 展开全部按钮
  elements.paramConfigContainer.querySelectorAll('.json-tree-expand-all').forEach(btn => {
    btn.addEventListener('click', () => {
      const treeName = btn.dataset.treeName
      const tree = elements.paramConfigContainer.querySelector(`[data-json-tree="${treeName}"]`)
      tree.querySelectorAll('.json-tree-children').forEach(child => {
        child.style.display = 'block'
      })
      tree.querySelectorAll('.json-tree-arrow').forEach(arrow => {
        arrow.style.transform = 'rotate(90deg)'
      })
      tree.querySelectorAll('.json-tree-branch').forEach(node => {
        node.classList.add('expanded')
      })
    })
  })
  
  // 折叠全部按钮
  elements.paramConfigContainer.querySelectorAll('.json-tree-collapse-all').forEach(btn => {
    btn.addEventListener('click', () => {
      const treeName = btn.dataset.treeName
      const tree = elements.paramConfigContainer.querySelector(`[data-json-tree="${treeName}"]`)
      tree.querySelectorAll('.json-tree-children').forEach(child => {
        child.style.display = 'none'
      })
      tree.querySelectorAll('.json-tree-arrow').forEach(arrow => {
        arrow.style.transform = 'rotate(0deg)'
      })
      tree.querySelectorAll('.json-tree-branch').forEach(node => {
        node.classList.remove('expanded')
      })
    })
  })
  
  // 验证规则选择器
  elements.paramConfigContainer.querySelectorAll('.validation-option').forEach(btn => {
    btn.addEventListener('click', () => {
      const validation = btn.dataset.validation
      const path = btn.dataset.path
      const treeName = btn.dataset.tree
      
      // 更新按钮状态
      const selector = btn.closest('.json-tree-validation-selector')
      selector.querySelectorAll('.validation-option').forEach(b => b.classList.remove('active'))
      btn.classList.add('active')
      selector.dataset.current = validation
      
      // 更新数据
      updateJsonTreeValidation(treeName, path, validation)
    })
  })
  
  // saveAs 输入框
  elements.paramConfigContainer.querySelectorAll('.json-tree-saveas-input').forEach(input => {
    input.addEventListener('change', () => {
      const path = input.dataset.path
      const treeName = input.dataset.tree
      const saveAs = input.value.trim()
      
      updateJsonTreeSaveAs(treeName, path, saveAs)
    })
  })
  
  // 模板选择器
  bindTemplateSelectEvents()
}

function updateJsonTreeValidation(treeName, path, validation) {
  const hiddenInput = elements.paramConfigContainer.querySelector(`[data-name="${treeName}"][data-json-tree-value]`)
  if (!hiddenInput) return
  
  try {
    const currentData = JSON.parse(hiddenInput.value || '{}')
    setNestedProperty(currentData, path, 'validation', validation)
    hiddenInput.value = JSON.stringify(currentData)
  } catch (e) {
    console.error('[v0] 更新验证规则失败:', e)
  }
}

function updateJsonTreeSaveAs(treeName, path, saveAs) {
  const hiddenInput = elements.paramConfigContainer.querySelector(`[data-name="${treeName}"][data-json-tree-value]`)
  if (!hiddenInput) return
  
  try {
    const currentData = JSON.parse(hiddenInput.value || '{}')
    const fieldKey = path.split('.').pop() // 获取字段名
    
    // 获取旧的saveAs值
    const oldSaveAs = getNestedProperty(currentData, path, 'saveAs')
    
    // 更新数据
    setNestedProperty(currentData, path, 'saveAs', saveAs || undefined)
    hiddenInput.value = JSON.stringify(currentData)
    
    // 同步更新全局变量列表，使其立即在其他输入框的autocomplete中可用
    syncSaveAsVariable(oldSaveAs, saveAs, treeName, fieldKey)
  } catch (e) {
    console.error('[v0] 更新saveAs失败:', e)
  }
}

function getNestedProperty(obj, path, property) {
  const keys = path.split('.')
  let current = obj
  
  for (let i = 0; i < keys.length; i++) {
    if (!current || !current[keys[i]]) return undefined
    current = current[keys[i]]
  }
  
  return current ? current[property] : undefined
}

function syncSaveAsVariable(oldName, newName, treeName, fieldKey) {
  // 移除旧变量（如果存在）
  if (oldName) {
    allDefinedVariables = allDefinedVariables.filter(v => v.name !== oldName)
  }
  
  // 添加新变量（如果有值）
  if (newName && newName.trim()) {
    // 确定组件类型描述
    const componentTypeDesc = treeName === 'rRsp' ? 'SOAP/REST请求响应' : '组件响应'
    
    // 检查是否已存在
    const exists = allDefinedVariables.find(v => v.name === newName)
    if (!exists) {
      allDefinedVariables.push({
        name: newName,
        description: `${componentTypeDesc}字段 ${fieldKey}`
      })
    }
  }
}

function setNestedProperty(obj, path, property, value) {
  const keys = path.split('.')
  let current = obj
  
  for (let i = 0; i < keys.length - 1; i++) {
    if (!current[keys[i]]) current[keys[i]] = {}
    current = current[keys[i]]
  }
  
  const lastKey = keys[keys.length - 1]
  if (current[lastKey] && typeof current[lastKey] === 'object') {
    if (value === undefined) {
      delete current[lastKey][property]
    } else {
      current[lastKey][property] = value
    }
  }
}

function bindGlobalShowAllFieldsToggle() {
  const globalToggle = elements.paramConfigContainer.querySelector('.json-tree-show-all-fields-global')
  if (!globalToggle) return
  
  globalToggle.addEventListener('change', () => {
    const showAllFields = globalToggle.checked
    
    // 遍历所有json树
    elements.paramConfigContainer.querySelectorAll('[data-json-tree]').forEach(tree => {
      tree.querySelectorAll('.json-tree-leaf').forEach(leaf => {
        const isDefault = leaf.dataset.isDefault === 'true'
        const input = leaf.querySelector('.json-tree-input')
        const hasValue = input && input.value && input.value.trim() !== ''
        
        if (showAllFields) {
          // 显示全部字段
          leaf.style.display = 'block'
        } else {
          // 仅显示有值的字段或非默认字段
          leaf.style.display = (hasValue || !isDefault) ? 'block' : 'none'
        }
      })
    })
    
    // 更新切换文字
    const toggleText = globalToggle.parentElement.querySelector('.json-tree-toggle-text')
    if (toggleText) {
      toggleText.textContent = showAllFields ? '显示全部字段' : '仅显示已填写'
    }
  })
}

function bindTemplateSelectEvents() {
  elements.paramConfigContainer.querySelectorAll('.param-template-select').forEach(select => {
  const name = select.dataset.name
  const customInput = elements.paramConfigContainer.querySelector(`[data-name="${name}-custom"]`)
  
  select.addEventListener('change', () => {
  if (select.value && customInput) {
  customInput.value = ''
  }
  // 当选择模板时，可以在这里触发参数更新
  // 目前保持简单实现，后续可扩展为根据模板动态加载参数
  })
  
  if (customInput) {
  customInput.addEventListener('input', () => {
  if (customInput.value) {
  select.value = ''
  }
  })
  }
  })
  }

function updateJsonTreeValue(treeName) {
  const tree = elements.paramConfigContainer.querySelector(`[data-json-tree="${treeName}"]`)
  const hiddenInput = elements.paramConfigContainer.querySelector(`[data-name="${treeName}"][data-json-tree-value]`)
  
  if (!tree || !hiddenInput) return
  
  try {
    const currentData = JSON.parse(hiddenInput.value || '{}')
    
    tree.querySelectorAll('.json-tree-input').forEach(input => {
      const path = input.dataset.path
      const value = input.value
      setNestedValue(currentData, path, value)
    })
    
    hiddenInput.value = JSON.stringify(currentData)
  } catch (e) {
    console.error('[v0] 更新JSON树值失败:', e)
  }
}

function setNestedValue(obj, path, value) {
  const keys = path.split('.')
  let current = obj
  
  for (let i = 0; i < keys.length - 1; i++) {
    if (!current[keys[i]]) current[keys[i]] = {}
    current = current[keys[i]]
  }
  
  const lastKey = keys[keys.length - 1]
  if (current[lastKey] && typeof current[lastKey] === 'object' && current[lastKey].type) {
    current[lastKey].value = value
  } else {
    current[lastKey] = value
  }
}

function bindComboBoxEvents() {
  const comboWrappers = elements.paramConfigContainer.querySelectorAll('[data-combo]')
  
  comboWrappers.forEach(wrapper => {
    const input = wrapper.querySelector('.param-combo-input')
    const toggle = wrapper.querySelector('.param-combo-toggle')
    const dropdown = wrapper.querySelector('.param-combo-dropdown')
    
    if (!input || !toggle || !dropdown) {
      return
    }
    
  // 切换下拉框显示
  toggle.addEventListener('click', (e) => {
    e.stopPropagation()
    wrapper.classList.toggle('open')
  })
    
    // 输入时过滤选项
    input.addEventListener('input', () => {
      const searchText = input.value.toLowerCase()
      const options = dropdown.querySelectorAll('.param-combo-option')
      options.forEach(opt => {
        const text = opt.textContent.toLowerCase()
        opt.style.display = text.includes(searchText) ? 'block' : 'none'
      })
      wrapper.classList.add('open')
    })
    
    // 选择选项
    dropdown.querySelectorAll('.param-combo-option').forEach(option => {
      option.addEventListener('click', () => {
        input.value = option.dataset.value
        wrapper.classList.remove('open')
      })
    })
    
    // 点击外部关闭下拉框
    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) {
        wrapper.classList.remove('open')
      }
    })
  })
}



function bindAutocompleteEvents() {
  const autocompleteInputs = elements.paramConfigContainer.querySelectorAll('[data-autocomplete]')
  
  autocompleteInputs.forEach(input => {
  // 支持param-autocomplete-wrapper和json-tree-input-wrapper两种容器
  const wrapper = input.closest('.param-autocomplete-wrapper') || input.closest('.json-tree-input-wrapper')
  const dropdown = wrapper?.querySelector('.param-autocomplete-dropdown') || wrapper?.querySelector('.json-tree-autocomplete-dropdown')
    
    if (!dropdown) return
    
    let lastCursorPos = 0
    let lastSearchText = ''
    
    const showAutocomplete = (searchText, cursorPos) => {
      const filtered = allDefinedVariables.filter(v => 
        v.name.toLowerCase().includes(searchText.toLowerCase())
      )
      
      if (filtered.length === 0) {
        dropdown.style.display = 'none'
        return
      }
      
      dropdown.innerHTML = filtered.map(v => `
        <div class="param-autocomplete-option" data-var-name="${v.name}">
          <div class="param-autocomplete-var-name">${v.name}</div>
          ${v.description ? `<div class="param-autocomplete-var-desc">${v.description}</div>` : ''}
        </div>
      `).join('')
      
      // 绑定点击事件
      dropdown.querySelectorAll('.param-autocomplete-option').forEach(option => {
        option.addEventListener('click', () => {
          const varName = option.dataset.varName
          const currentValue = input.value
          const beforeCursor = currentValue.substring(0, lastCursorPos - lastSearchText.length - 2)
          const afterCursor = currentValue.substring(lastCursorPos)
          
          input.value = beforeCursor + '${' + varName + '}' + afterCursor
          dropdown.style.display = 'none'
          
          // 设置光标位置到变量后面
          const newCursorPos = beforeCursor.length + varName.length + 3
          input.setSelectionRange(newCursorPos, newCursorPos)
          input.focus()
        })
      })
      
      // 定位下拉框
      dropdown.style.display = 'block'
    }
    
    const handleInput = () => {
      const value = input.value
      const cursorPos = input.selectionStart
      
      // 查找光标前最近的 ${ 位置
      const beforeCursor = value.substring(0, cursorPos)
      const lastDollarBrace = beforeCursor.lastIndexOf('${')
      
      if (lastDollarBrace === -1) {
        dropdown.style.display = 'none'
        return
      }
      
      // 检查 ${ 后是否有 }
      const afterDollarBrace = value.substring(lastDollarBrace)
      const closingBrace = afterDollarBrace.indexOf('}')
      
      // 如果 } 在光标前，说明已经完成输入，不��示自动完成
      if (closingBrace !== -1 && closingBrace < cursorPos - lastDollarBrace) {
        dropdown.style.display = 'none'
        return
      }
      
      // 提取搜索文本（${ 和光标之间的内容）
      const searchText = beforeCursor.substring(lastDollarBrace + 2)
      lastSearchText = searchText
      lastCursorPos = cursorPos
      
      showAutocomplete(searchText, cursorPos)
    }
    
    input.addEventListener('input', handleInput)
    input.addEventListener('keyup', handleInput)
    
    // 点击外部关闭
    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target)) {
        dropdown.style.display = 'none'
      }
    })
  })
}

function bindVariableListEvents() {
  const addBtn = elements.paramConfigContainer.querySelector('[data-add-variable]')
  const variablesList = elements.paramConfigContainer.querySelector('[data-variables-list]')
  
  if (addBtn && variablesList) {
    addBtn.addEventListener('click', () => {
      const newItem = document.createElement('div')
      newItem.className = 'param-variable-item'
      newItem.innerHTML = `
        <div class="param-variable-inputs">
          <input type="text" placeholder="变量名 (My_)" data-var-name>
          <input type="text" placeholder="变量值" data-var-value>
          <input type="text" placeholder="变量描述" data-var-desc>
        </div>
        <button type="button" class="param-variable-remove" data-remove-var>×</button>
      `
      variablesList.appendChild(newItem)
      
      newItem.querySelector('[data-remove-var]').addEventListener('click', () => {
        newItem.remove()
      })
    })
    
    // 绑定删除按钮
    variablesList.querySelectorAll('[data-remove-var]').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.closest('.param-variable-item').remove()
      })
    })
  }
}

function collectParamFormData() {
  const formData = {}
  
  // 收集普通输入框
  elements.paramConfigContainer.querySelectorAll('.param-field-input').forEach(input => {
  const name = input.dataset.name
  formData[name] = input.value.trim()
  })
  
  // 收集combo box输入框
  elements.paramConfigContainer.querySelectorAll('[data-combo]').forEach(combo => {
  const name = combo.dataset.name
  const input = combo.querySelector('.param-combo-input')
  if (input) {
  formData[name] = input.value.trim()
  }
  })
  
  // 收集文本域
  elements.paramConfigContainer.querySelectorAll('.param-field-textarea').forEach(textarea => {
  const name = textarea.dataset.name
  formData[name] = textarea.value.trim()
  })
  
  // 收集模板选择器
  elements.paramConfigContainer.querySelectorAll('.param-template-select').forEach(select => {
    const name = select.dataset.name
    const customInput = elements.paramConfigContainer.querySelector(`[data-name="${name}-custom"]`)
    // 优先使用下拉选择的值，如果为空则使用自定义输入
    if (select.value) {
      formData[name] = select.value
    } else if (customInput && customInput.value.trim()) {
      formData[name] = customInput.value.trim()
    }
  })
  
  // 收集变量列表
  const variablesList = elements.paramConfigContainer.querySelector('[data-variables-list]')
  if (variablesList) {
    const variables = []
    const variableDescriptions = []
    variablesList.querySelectorAll('.param-variable-item').forEach(item => {
      const nameInput = item.querySelector('[data-var-name]')
      const valueInput = item.querySelector('[data-var-value]')
      const descInput = item.querySelector('[data-var-desc]')
      if (nameInput && valueInput) {
        let varName = nameInput.value.trim()
        const varValue = valueInput.value.trim()
        const varDesc = descInput ? descInput.value.trim() : ''
        
        // 如果变量名不为空且不以 My_ 开头，自动添加 My_ 前缀
        if (varName && !varName.startsWith('My_')) {
          varName = `My_${varName}`
        }
        
        if (varName && varValue) {
          variables.push(`${varName}=${varValue}`)
          if (varDesc) {
            variableDescriptions.push(`${varName}:${varDesc}`)
          }
        }
      }
    })
    formData.vars = variables.join(';')
    formData.varDescriptions = variableDescriptions.join(';')
  }
  
  // 收集JSON树数据
  elements.paramConfigContainer.querySelectorAll('[data-json-tree-value]').forEach(input => {
    const name = input.dataset.name
    try {
      formData[name] = JSON.parse(input.value || '{}')
    } catch (e) {
      formData[name] = {}
    }
  })
  
  return formData
}

function updateParamSummary(params) {
  const summary = []
  
  for (const [key, value] of Object.entries(params)) {
    if (value) {
      const displayValue = typeof value === 'string' && value.length > 50 
        ? value.substring(0, 50) + '...' 
        : value
      summary.push(`<div><strong>${key}:</strong> ${displayValue}</div>`)
    }
  }
  
  if (summary.length > 0) {
    elements.paramSummary.innerHTML = summary.join('')
  } else {
    elements.paramSummary.innerHTML = '<div style="color:#95a5a6;">暂无配置参数</div>'
  }
}

// 设置上传区域
function setupUploadZone(zone, input, display, fileName) {
  zone.addEventListener("click", () => input.click())

  zone.addEventListener("dragover", (e) => {
    e.preventDefault()
    zone.classList.add("dragover")
  })

  zone.addEventListener("dragleave", () => {
    zone.classList.remove("dragover")
  })

  zone.addEventListener("drop", (e) => {
    e.preventDefault()
    zone.classList.remove("dragover")
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0], zone, display, fileName)
    }
  })

  input.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelect(e.target.files[0], zone, display, fileName)
    }
  })
}

function handleFileSelect(file, zone, display, fileName) {
  zone.style.display = "none"
  display.style.display = "flex"
  fileName.textContent = file.name
}

function removeFile(type) {
  if (type === "history") {
    elements.historyUploadZone.style.display = "block"
    elements.historyFileDisplay.style.display = "none"
    elements.historyFileInput.value = ""
  } else if (type === "case") {
    elements.caseUploadZone.style.display = "block"
    elements.caseFileDisplay.style.display = "none"
    elements.caseFileInput.value = ""
  } else if (type === "aw") {
    elements.awUploadZone.style.display = "block"
    elements.awFileDisplay.style.display = "none"
    elements.awFileInput.value = ""
  }
}

// 模拟API调用
async function mockApiCall(endpoint, data) {
  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 500 + Math.random() * 1000))
  return { success: true, data }
}

function toggleTips() {
  if (elements.tipsCard) {
    elements.tipsCard.classList.toggle("collapsed")
  }
}

function getCurrentTime() {
  const now = new Date()
  const hours = now.getHours().toString().padStart(2, "0")
  const minutes = now.getMinutes().toString().padStart(2, "0")
  return `${hours}:${minutes}`
}

// 开始生成
async function startGeneration() {
  const caseFileUploaded = elements.caseFileDisplay.style.display === "flex"
  const apiVersionSelected = document.getElementById("apiVersionSelect").value !== ""

  if (!caseFileUploaded) {
    showNotification("请先上传需要生成的用例文件", "error", 2000)
    return
  }

  if (!apiVersionSelected) {
    showNotification("请选择接口文档版本", "error", 2000)
    return
  }

  hideActionButtons()

  // 禁用生成按钮
  elements.generateBtn.disabled = true
  elements.generateBtn.textContent = "生成中..."

  // 启用输入框
  elements.chatInput.disabled = false
  elements.chatInput.placeholder = "输入消息，按 Enter 发送..."
  elements.sendBtn.disabled = false
  isGenerating = true

  if (isFirstGeneration) {
    elements.chatMessages.innerHTML = ""
    isFirstGeneration = false
  }

  // 模拟调用后台接口
  addMessage("正在连接AI服务...", "ai")
  await mockApiCall("/api/connect", {})

  addMessage("正在分析您上传的用例文件，请稍候...", "ai")
  await mockApiCall("/api/analyze", { file: "case.xml" })

  // 模拟Agent多轮对话
  addMessage(
    "我已经分析了您的用例模板。为了生成更准确的测试用例，请问：\n\n1. 这个系统主要的用户群体是谁？\n2. 是否有特殊的安全性要求？",
    "ai",
  )
}

// 发送消息
async function sendMessage() {
  const message = elements.chatInput.value.trim()
  if (!message) return

  addMessage(message, "user")
  elements.chatInput.value = ""

  // 模拟AI回复和多轮对话
  await mockApiCall("/api/chat", { message })

  const responses = [
    "好的，我已记录您的需求。还有其他需要补充的信息吗？如果没有，请回复'开始生成'，我将为您生成测试用例。",
    "收到，这对生成高质量的测试用例很有帮助。如果准备好了，请回复'开始生成'。",
    "明白了，我会根据这些信息优化测试用例。请回复'开始生成'开始生成过程。",
  ]

  if (message.includes("开始生成") || message.includes("生成")) {
    await startGeneratingCases()
  } else {
    const randomResponse = responses[Math.floor(Math.random() * responses.length)]
    addMessage(randomResponse, "ai")
  }
}

// 开始生成用例
async function startGeneratingCases() {
  addMessage("好的，开始生成测试用例，请稍候...", "ai")

  progressCounter++
  const progressId = `generateProgress_${progressCounter}`
  const progressFillId = `progressFill_${progressCounter}`
  const progressPercentId = `progressPercent_${progressCounter}`

  // 添加进度显示
  const currentTime = getCurrentTime()
  const progressHtml = `
    <div class="progress-container" id="${progressId}">
      <div class="progress-text">正在生成测试用例... <span id="${progressPercentId}">0%</span></div>
      <div class="progress-bar">
        <div class="progress-fill" id="${progressFillId}" style="width: 0%"></div>
      </div>
    </div>
  `
  const progressDiv = document.createElement("div")
  progressDiv.className = "message ai-message"
  progressDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">${progressHtml}<div class="message-time">${currentTime}</div></div>
  `
  elements.chatMessages.appendChild(progressDiv)
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight

  const progressFill = document.getElementById(progressFillId)
  const progressPercent = document.getElementById(progressPercentId)

  for (let i = 0; i <= 100; i += 10) {
    await new Promise((resolve) => setTimeout(resolve, 300))
    if (progressFill && progressPercent) {
      progressFill.style.width = i + "%"
      progressPercent.textContent = i + "%"
    }
  }

  // 加载mock数据作为生成结果
  testCases = JSON.parse(JSON.stringify(mockTestCases))

  addTestCaseCard()

  // 显示操作按钮
  showActionButtons()
  elements.generateBtn.disabled = false
  elements.generateBtn.textContent = "开始生成"
}

function addTestCaseCard() {
  const cardHtml = `
    <div class="test-case-card">
      <div class="test-case-card-header">
        <h4>测试用例生成完成</h4>
        <span>共 ${testCases.length} 个用例</span>
      </div>
      <div class="test-case-card-body">
        ${testCases
          .map(
            (tc, index) => `
          <div class="test-case-item" data-index="${index}">
            <div class="test-case-item-icon">${index + 1}</div>
            <div class="test-case-item-info">
              <div class="test-case-item-name">${tc.name}</div>
              <div class="test-case-item-id">${tc.id}</div>
            </div>
            <div class="test-case-item-arrow">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </div>
          </div>
        `,
          )
          .join("")}
      </div>
      <div class="test-case-card-footer">
        <span>点击用例查看详情和编辑</span>
      </div>
    </div>
  `

  const messageDiv = document.createElement("div")
  messageDiv.className = "message ai-message"
  messageDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">
      <p>测试用例生成完成！您可以点击下方卡片中的用例查看详情和编辑，或点击"继续生成"生成最终用例文件。</p>
      ${cardHtml}
    </div>
  `
  elements.chatMessages.appendChild(messageDiv)
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight

  // 绑定卡片中用例项的点击事件
  messageDiv.querySelectorAll(".test-case-item").forEach((item) => {
    item.addEventListener("click", () => {
      const index = Number.parseInt(item.dataset.index)
      currentCaseIndex = index
      openModal()
    })
  })
}

function addMessage(text, type) {
  const currentTime = getCurrentTime()
  const messageDiv = document.createElement("div")
  messageDiv.className = `message ${type}-message`
  messageDiv.innerHTML = `
    <div class="message-avatar">${type === "ai" ? "Agent" : "我"}</div>
    <div class="message-content">
      <p>${text.replace(/\n/g, "<br>")}</p>
      <div class="message-time">${currentTime}</div>
    </div>
  `
  elements.chatMessages.appendChild(messageDiv)
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight
}

function showActionButtons() {
  generationComplete = true
  elements.chatActionButtons.style.display = "flex"
  elements.continueGenerateBtn.style.display = "inline-flex"
  elements.chatInputArea.classList.add("hidden")
}

function hideActionButtons() {
  generationComplete = false
  elements.chatActionButtons.style.display = "none"
  elements.continueGenerateBtn.style.display = "none"
  elements.chatInputArea.classList.remove("hidden")
  canDownload = false
}

function showContinueConfirm() {
  elements.confirmMessage.textContent = "是否已经完成用例的修改和确认？"
  elements.confirmOverlay.classList.add("active")
}

function closeConfirm() {
  elements.confirmOverlay.classList.remove("active")
}

async function confirmContinueGenerate() {
  closeConfirm()

  // 先隐藏所有按钮
  elements.chatActionButtons.style.display = "none"
  elements.chatInputArea.classList.add("hidden")

  addMessage("好的，正在基于当前用例继续生成...", "ai")

  progressCounter++
  const progressId = `continueProgress_${progressCounter}`
  const progressFillId = `continueProgressFill_${progressCounter}`
  const progressPercentId = `continueProgressPercent_${progressCounter}`

  // 添加进度显示
  const currentTime = getCurrentTime()
  const progressHtml = `
    <div class="progress-container" id="${progressId}">
      <div class="progress-text">正在生成用例文件... <span id="${progressPercentId}">0%</span></div>
      <div class="progress-bar">
        <div class="progress-fill" id="${progressFillId}" style="width: 0%"></div>
      </div>
    </div>
  `
  const progressDiv = document.createElement("div")
  progressDiv.className = "message ai-message"
  progressDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">${progressHtml}<div class="message-time">${currentTime}</div></div>
  `
  elements.chatMessages.appendChild(progressDiv)
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight

  const progressFill = document.getElementById(progressFillId)
  const progressPercent = document.getElementById(progressPercentId)

  for (let i = 0; i <= 100; i += 5) {
    await new Promise((resolve) => setTimeout(resolve, 200))
    if (progressFill && progressPercent) {
      progressFill.style.width = i + "%"
      progressPercent.textContent = i + "%"
    }
  }

  addDownloadCard()

  canDownload = true
  elements.chatActionButtons.style.display = "none"
  elements.chatInputArea.classList.remove("hidden")
}

function addDownloadCard() {
  const currentTime = getCurrentTime()
  const fileName = `test_cases_${new Date().toISOString().slice(0, 10)}.xml`

  const cardHtml = `
    <div class="download-card">
      <div class="download-card-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <div class="download-card-header-info">
          <h4>用例文件生成完成</h4>
          <span>共 ${testCases.length} 个测试用例</span>
        </div>
      </div>
      <div class="download-card-body">
        <div class="download-card-info">
          <div class="download-card-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
          </div>
          <div class="download-card-details">
            <div class="download-card-filename">${fileName}</div>
            <div class="download-card-meta">XML 格式 · 点击下方按钮下载</div>
          </div>
        </div>
        <button class="download-card-btn" id="downloadCardBtn">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          下载用例文件
        </button>
      </div>
    </div>
  `

  const messageDiv = document.createElement("div")
  messageDiv.className = "message ai-message"
  messageDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">
      <p>用例文件生成完成！您可以点击下方卡片下���。</p>
      ${cardHtml}
      <div class="message-time">${currentTime}</div>
    </div>
  `
  elements.chatMessages.appendChild(messageDiv)
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight

  // 绑定下载按钮事件
  messageDiv.querySelector("#downloadCardBtn").addEventListener("click", downloadFile)
}

function downloadFile() {
  // 生成XML格式的用例文件
  const xmlContent = generateXmlContent()
  const blob = new Blob([xmlContent], { type: "application/xml" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "test_cases_" + new Date().toISOString().slice(0, 10) + ".xml"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  addMessage("文件下载已开始！", "ai")
}

function generateXmlContent() {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<testcases>\n'

  testCases.forEach((tc) => {
    xml += `  <testcase id="${tc.id}" name="${tc.name}">\n`

    xml += "    <preconditions>\n"
    tc.preconditions.forEach((pre, i) => {
      xml += `      <precondition index="${i + 1}" name="${pre.name}">\n`
      pre.components.forEach((comp) => {
        xml += `        <component type="${comp.type}" name="${comp.name}">\n`
        xml += `          <params>${JSON.stringify(comp.params)}</params>\n`
        xml += "        </component>\n"
      })
      xml += "      </precondition>\n"
    })
    xml += "    </preconditions>\n"

    xml += "    <steps>\n"
    tc.steps.forEach((step, i) => {
      xml += `      <step index="${i + 1}" name="${step.name}">\n`
      step.components.forEach((comp) => {
        xml += `        <component type="${comp.type}" name="${comp.name}">\n`
        xml += `          <params>${JSON.stringify(comp.params)}</params>\n`
        xml += "        </component>\n"
      })
      xml += "      </step>\n"
    })
    xml += "    </steps>\n"

    xml += "    <expectedResults>\n"
    tc.expectedResults.forEach((exp, i) => {
      xml += `      <expectedResult index="${i + 1}" name="${exp.name}">\n`
      exp.components.forEach((comp) => {
        xml += `        <component type="${comp.type}" name="${comp.name}">\n`
        xml += `          <params>${JSON.stringify(comp.params)}</params>\n`
        xml += "        </component>\n"
      })
      xml += "      </expectedResult>\n"
    })
    xml += "    </expectedResults>\n"

    xml += "  </testcase>\n"
  })

  xml += "</testcases>"
  return xml
}

// 模态框操作
function openModal() {
  // 保存当前数据的深拷贝作为备份
  testCasesBackup = JSON.parse(JSON.stringify(testCases))
  elements.modalOverlay.classList.add("active")
  renderCaseList()
  renderCaseDetail()
}

function cancelAndCloseModal() {
  // 恢复备份数据
  if (testCasesBackup !== null) {
    testCases = JSON.parse(JSON.stringify(testCasesBackup))
    testCasesBackup = null
  }
  elements.modalOverlay.classList.remove("active")
}

function closeModal() {
  elements.modalOverlay.classList.remove("active")
}

function saveAndCloseModal() {
  // 保存成功，清除备份
  testCasesBackup = null
  showNotification("保存成功", "success", 2000)
  closeModal()
}

function renderCaseList() {
  elements.caseList.innerHTML = testCases
    .map(
      (tc, index) => `
    <div class="case-item ${index === currentCaseIndex ? "active" : ""}" data-index="${index}">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
        <polyline points="10 9 9 9 8 9"></polyline>
      </svg>
      <span>${tc.name}</span>
    </div>
  `,
    )
    .join("")

  document.querySelectorAll(".case-item").forEach((item) => {
    item.addEventListener("click", () => {
      currentCaseIndex = Number.parseInt(item.dataset.index)
      renderCaseList()
      renderCaseDetail()
    })
  })
}

function renderCaseDetail() {
  const tc = testCases[currentCaseIndex]
  elements.detailTitle.textContent = tc.name
  elements.detailId.textContent = `用例 ID: ${tc.id}`

  renderSection(tc.preconditions, elements.preconditionList, "preconditions")
  renderSection(tc.steps, elements.stepsList, "steps")
  renderSection(tc.expectedResults, elements.expectedResultList, "expectedResults")
}

// 统一渲染区块（预置条件、测试步骤、预期结果结构相同）
function renderSection(items, container, sectionType) {
  if (!items || items.length === 0) {
    const hintText = sectionType === "preconditions" ? "预置条件" : sectionType === "steps" ? "测试步骤" : "预期结果"
    container.innerHTML = `<p class="empty-hint">暂��${hintText}，点击上方按钮添加</p>`
    return
  }

  container.innerHTML = items
    .map(
      (item, stepIndex) => `
    <div class="step-item" draggable="true" data-type="${sectionType}" data-section="${sectionType}" data-step-index="${stepIndex}">
      <div class="step-header">
        <div class="drag-handle">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="9" cy="5" r="1"></circle>
            <circle cx="9" cy="12" r="1"></circle>
            <circle cx="9" cy="19" r="1"></circle>
            <circle cx="15" cy="5" r="1"></circle>
            <circle cx="15" cy="12" r="1"></circle>
            <circle cx="15" cy="19" r="1"></circle>
          </svg>
        </div>
        <button class="expand-btn ${item.expanded ? "expanded" : ""}" data-section="${sectionType}" data-step-index="${stepIndex}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <span class="step-number">${stepIndex + 1}</span>
        <span class="step-name">${item.name}</span>
        <div class="step-actions">
          <button class="icon-btn edit-step-btn" data-section="${sectionType}" data-step-index="${stepIndex}" title="编辑">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="icon-btn copy-step-btn" data-section="${sectionType}" data-step-index="${stepIndex}" title="复制">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
          <button class="icon-btn danger delete-step-btn" data-section="${sectionType}" data-step-index="${stepIndex}" title="删除">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>
      <div class="step-content ${item.expanded ? "expanded" : ""}">
        <div class="components-list" data-section="${sectionType}" data-step-index="${stepIndex}">
          ${
            item.components && item.components.length > 0
              ? item.components
                  .map(
                    (comp, compIndex) => `
            <div class="component-item" draggable="true" data-type="component" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}">
              <div class="drag-handle">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="9" cy="5" r="1"></circle>
                  <circle cx="9" cy="12" r="1"></circle>
                  <circle cx="9" cy="19" r="1"></circle>
                  <circle cx="15" cy="5" r="1"></circle>
                  <circle cx="15" cy="12" r="1"></circle>
                  <circle cx="15" cy="19" r="1"></circle>
                </svg>
              </div>
              <span class="component-number">${compIndex + 1}</span>
              <div class="component-info">
                <div class="component-name">${comp.name}</div>
                <pre class="component-params">${JSON.stringify(comp.params, null, 2)}</pre>
              </div>
              <div class="component-actions">
                <button class="icon-btn edit-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="编辑">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                </button>
                <button class="icon-btn copy-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="复制">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                </button>
                <button class="icon-btn danger delete-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="���除">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            </div>
          `,
                  )
                  .join("")
              : '<p class="empty-hint" style="font-size: 12px; padding: 8px;">暂无组件</p>'
          }
        </div>
        <button class="add-btn add-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}">+ 添加组件</button>
      </div>
    </div>
  `,
    )
    .join("")

  bindSectionEvents(container, sectionType)
}

function bindSectionEvents(container, sectionType) {
  // 展开/折叠
  container.querySelectorAll(".expand-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = Number.parseInt(btn.dataset.stepIndex)
      const section = btn.dataset.section
      testCases[currentCaseIndex][section][stepIndex].expanded =
        !testCases[currentCaseIndex][section][stepIndex].expanded
      renderCaseDetail()
    })
  })

  // 编辑步骤
  container.querySelectorAll(".edit-step-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      openStepEdit(Number.parseInt(btn.dataset.stepIndex), btn.dataset.section)
    })
  })

  // 复制步骤
  container.querySelectorAll(".copy-step-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = Number.parseInt(btn.dataset.stepIndex)
      const section = btn.dataset.section
      const item = testCases[currentCaseIndex][section][stepIndex]
      const newItem = JSON.parse(JSON.stringify(item))
      newItem.id = "item" + Date.now()
      newItem.name = item.name + " (副本)"
      testCases[currentCaseIndex][section].splice(stepIndex + 1, 0, newItem)
      renderCaseDetail()
    })
  })

  // 删除步骤
  container.querySelectorAll(".delete-step-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation()
      const confirmed = await showConfirmDialog("确定要删除此步骤吗？", "删除确认")
      if (confirmed) {
        const stepIndex = Number.parseInt(btn.dataset.stepIndex)
        const section = btn.dataset.section
        testCases[currentCaseIndex][section].splice(stepIndex, 1)
        renderCaseDetail()
      }
    })
  })

  // 添加组件
  container.querySelectorAll(".add-comp-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      openComponentEdit(Number.parseInt(btn.dataset.stepIndex), null, btn.dataset.section)
    })
  })

  // 编辑组件
  container.querySelectorAll(".edit-comp-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      openComponentEdit(
        Number.parseInt(btn.dataset.stepIndex),
        Number.parseInt(btn.dataset.compIndex),
        btn.dataset.section,
      )
    })
  })

  // 复制组件
  container.querySelectorAll(".copy-comp-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = Number.parseInt(btn.dataset.stepIndex)
      const compIndex = Number.parseInt(btn.dataset.compIndex)
      const section = btn.dataset.section
      const comp = testCases[currentCaseIndex][section][stepIndex].components[compIndex]
      const newComp = JSON.parse(JSON.stringify(comp))
      newComp.id = "c" + Date.now()
      newComp.name = comp.name + " (副本)"
      testCases[currentCaseIndex][section][stepIndex].components.splice(compIndex + 1, 0, newComp)
      renderCaseDetail()
    })
  })

  // 删除组件
  container.querySelectorAll(".delete-comp-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation()
      const confirmed = await showConfirmDialog("确定要删除此组件吗？", "删除确认")
      if (confirmed) {
        const stepIndex = Number.parseInt(btn.dataset.stepIndex)
        const compIndex = Number.parseInt(btn.dataset.compIndex)
        const section = btn.dataset.section
        testCases[currentCaseIndex][section][stepIndex].components.splice(compIndex, 1)
        renderCaseDetail()
      }
    })
  })

  container.querySelectorAll(".step-item").forEach((item) => {
    item.addEventListener("dragstart", handleDragStart)
    item.addEventListener("dragend", handleDragEnd)
    item.addEventListener("dragover", handleDragOver)
    item.addEventListener("drop", handleDrop)
  })

  container.querySelectorAll(".component-item").forEach((item) => {
    item.addEventListener("dragstart", (e) => {
      e.stopPropagation()
      handleDragStart(e)
    })
    item.addEventListener("dragend", (e) => {
      e.stopPropagation()
      handleDragEnd(e)
    })
    item.addEventListener("dragover", (e) => {
      e.stopPropagation()
      handleDragOver(e)
    })
    item.addEventListener("drop", (e) => {
      e.stopPropagation()
      handleDrop(e)
    })
  })
}

function handleDragStart(e) {
  // 阻止事件冒泡，避免组件拖拽触发父级步骤拖拽
  e.stopPropagation()

  draggedElement = e.target.closest('[draggable="true"]')
  draggedType = draggedElement.dataset.type
  draggedSection = draggedElement.dataset.section
  draggedStepIndex = draggedElement.dataset.stepIndex ? Number.parseInt(draggedElement.dataset.stepIndex) : null

  if (draggedType === "component") {
    draggedIndex = Number.parseInt(draggedElement.dataset.compIndex)
  } else {
    draggedIndex = Number.parseInt(draggedElement.dataset.stepIndex)
  }

  draggedElement.classList.add("dragging")
  e.dataTransfer.effectAllowed = "move"
  e.dataTransfer.setData("text/plain", "") // Firefox需要这个
}

function handleDragEnd(e) {
  e.stopPropagation()
  if (draggedElement) {
    draggedElement.classList.remove("dragging")
  }
  draggedElement = null
  draggedType = null
  draggedIndex = null
  draggedSection = null
  draggedStepIndex = null
}

function handleDragOver(e) {
  e.preventDefault()
  e.stopPropagation()
  e.dataTransfer.dropEffect = "move"
}

function handleDrop(e) {
  e.preventDefault()
  e.stopPropagation()

  if (!draggedElement) return

  const dropTarget = e.target.closest('[draggable="true"]')
  if (!dropTarget || dropTarget === draggedElement) return

  const dropType = dropTarget.dataset.type
  const dropSection = dropTarget.dataset.section

  // 只允许同类型拖拽（步骤对步骤，组件对组件）
  if (draggedType !== dropType) return

  // 只允许同section内拖拽
  if (draggedSection !== dropSection) return

  const tc = testCases[currentCaseIndex]

  if (draggedType === "component") {
    // 组件拖拽：必须在同一个步骤内
    const fromStepIndex = Number.parseInt(draggedElement.dataset.stepIndex)
    const fromCompIndex = Number.parseInt(draggedElement.dataset.compIndex)
    const toStepIndex = Number.parseInt(dropTarget.dataset.stepIndex)
    const toCompIndex = Number.parseInt(dropTarget.dataset.compIndex)

    // 只允许同一步骤内的组件拖拽
    if (fromStepIndex !== toStepIndex) return

    const components = tc[draggedSection][fromStepIndex].components
    const [removed] = components.splice(fromCompIndex, 1)
    components.splice(toCompIndex, 0, removed)
  } else {
    // 步骤拖拽
    const fromIndex = Number.parseInt(draggedElement.dataset.stepIndex)
    const toIndex = Number.parseInt(dropTarget.dataset.stepIndex)

    const [removed] = tc[draggedSection].splice(fromIndex, 1)
    tc[draggedSection].splice(toIndex, 0, removed)
  }

  renderCaseDetail()
}

// 步骤编辑
function openStepEdit(stepIndex, section) {
  editingStepIndex = stepIndex
  editingSection = section
  selectedPresetStep = null // 重置选中的预设步骤
  isEditingHistoryCase = false  // 确保这是测试用例详情页面的编辑
  
  // 关键修复：重新绑定保存按钮为saveStep
  elements.saveStepBtn.onclick = saveStep

  const titleMap = {
    preconditions: stepIndex !== null ? "编辑预置条件" : "添加预置条件",
    steps: stepIndex !== null ? "编辑测试步骤" : "添加测试步骤",
    expectedResults: stepIndex !== null ? "编辑预期结果" : "添加预期结果",
  }

  elements.stepEditTitle.textContent = titleMap[section]

  if (stepIndex !== null) {
    const item = testCases[currentCaseIndex][section][stepIndex]
    elements.stepNameInput.value = item.name
    elements.stepDescInput.value = item.description || ""
  } else {
    elements.stepNameInput.value = ""
    elements.stepDescInput.value = ""
  }

  // 渲染预置步骤下拉列表
  renderPresetStepsDropdown()

  elements.stepEditOverlay.classList.add("active")
}

function closeStepEdit() {
  elements.stepEditOverlay.classList.remove("active")
  editingStepIndex = null
  editingSection = null
}

function saveStep() {
  const name = elements.stepNameInput.value.trim()
  if (!name) {
    showNotification("请输入名称", "error", 2000)
    return
  }

  if (editingStepIndex !== null) {
    testCases[currentCaseIndex][editingSection][editingStepIndex].name = name
    testCases[currentCaseIndex][editingSection][editingStepIndex].description = elements.stepDescInput.value.trim()
  } else {
    let components = []
    if (selectedPresetStep && selectedPresetStep.components) {
      components = selectedPresetStep.components.map((comp, index) => ({
        id: "c" + Date.now() + "_" + index,
        type: comp.type,
        name: comp.name,
        params: JSON.parse(JSON.stringify(comp.params)),
      }))
    }

    const newItem = {
      id: "item" + Date.now(),
      name: name,
      description: elements.stepDescInput.value.trim(),
      expanded: true,
      components: components,
    }
    testCases[currentCaseIndex][editingSection].push(newItem)
  }

  closeStepEdit()
  renderCaseDetail()
}

// ============ 历史用例搜索功能 ============

function initHistorySearchElements() {
  elements.historySearchOverlay = document.getElementById("historySearchOverlay")
  elements.closeHistorySearchBtn = document.getElementById("closeHistorySearchBtn")
  elements.historySearchInput = document.getElementById("historySearchInput")
  elements.filterPanel = document.getElementById("filterPanel")
  elements.filterTags = document.getElementById("filterTags")
  elements.caseLibrarySelect = document.getElementById("caseLibrarySelect")
  elements.searchMethodSelect = document.getElementById("searchMethodSelect")
  elements.filterConfirmBtn = document.getElementById("filterConfirmBtn")
  elements.historySearchBtn = document.getElementById("historySearchBtn")
  elements.searchResults = document.getElementById("searchResults")
  elements.searchResultsList = document.getElementById("searchResultsList")
  elements.selectedCasesSection = document.getElementById("selectedCasesSection")
  elements.selectedCasesPreview = document.getElementById("selectedCasesPreview")
  elements.cancelHistorySearchBtn = document.getElementById("cancelHistorySearchBtn")
  elements.saveHistorySearchBtn = document.getElementById("saveHistorySearchBtn")
  elements.selectedHistoryCases = document.getElementById("selectedHistoryCases")
  elements.selectedCasesList = document.getElementById("selectedCasesList")
  elements.editHistorySelectionBtn = document.getElementById("editHistorySelectionBtn")
  
  // 历史用例详情弹窗（只读）
  elements.historyCaseDetailOverlay = document.getElementById("historyCaseDetailOverlay")
  elements.closeHistoryCaseDetailBtn = document.getElementById("closeHistoryCaseDetailBtn")
  elements.historyCaseList = document.getElementById("historyCaseList")
  elements.historyDetailTitle = document.getElementById("historyDetailTitle")
  elements.historyDetailId = document.getElementById("historyDetailId")
  elements.historyPreconditionList = document.getElementById("historyPreconditionList")
  elements.historyStepsList = document.getElementById("historyStepsList")
  elements.historyExpectedResultList = document.getElementById("historyExpectedResultList")
  elements.cancelHistoryCaseDetailBtn = document.getElementById("cancelHistoryCaseDetailBtn")
  
  // 上传区域
  elements.historyUploadZone = document.getElementById("historyUploadZone")
  elements.historyFileInput = document.getElementById("historyFileInput")
  elements.historyFileDisplay = document.getElementById("historyFileDisplay")
  elements.historyFileName = document.getElementById("historyFileName")
  elements.removeHistoryFile = document.getElementById("removeHistoryFile")
}

function bindHistorySearchEvents() {
  // 勾选复选框打开搜索弹窗
  elements.historyCheckbox.addEventListener("change", () => {
    if (elements.historyCheckbox.checked) {
      openHistorySearchModal()
    } else {
      selectedHistoryCases = []
      elements.selectedHistoryCases.style.display = "none"
    }
  })
  
  // 编辑按钮
  if (elements.editHistorySelectionBtn) {
    elements.editHistorySelectionBtn.addEventListener("click", openHistorySearchModal)
  }
  
  // 关闭弹窗
  elements.closeHistorySearchBtn.addEventListener("click", closeHistorySearchModal)
  elements.cancelHistorySearchBtn.addEventListener("click", closeHistorySearchModal)
  elements.historySearchOverlay.addEventListener("click", (e) => {
    if (e.target === elements.historySearchOverlay) closeHistorySearchModal()
  })
  
  // 保存选择
  elements.saveHistorySearchBtn.addEventListener("click", saveHistorySelection)
  
  // 搜索输入
  elements.historySearchInput.addEventListener("input", handleSearchInput)
  elements.historySearchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") performHistorySearch()
  })
  
  // 搜索按钮
  elements.historySearchBtn.addEventListener("click", performHistorySearch)
  
  // 筛选确认按钮
  elements.filterConfirmBtn.addEventListener("click", handleFilterConfirm)
  
  // 关闭筛选面板
  document.addEventListener("click", (e) => {
    if (!elements.historySearchInput.contains(e.target) && !elements.filterPanel.contains(e.target)) {
      elements.filterPanel.classList.remove("show")
    }
  })
  
  // 历史用例详情弹窗（只读）
  elements.closeHistoryCaseDetailBtn.addEventListener("click", closeHistoryCaseDetail)
  elements.cancelHistoryCaseDetailBtn.addEventListener("click", closeHistoryCaseDetail)
  elements.historyCaseDetailOverlay.addEventListener("click", (e) => {
    if (e.target === elements.historyCaseDetailOverlay) closeHistoryCaseDetail()
  })
  
  // 上传区域
  setupUploadZone(
    elements.historyUploadZone,
    elements.historyFileInput,
    elements.historyFileDisplay,
    elements.historyFileName
  )
  elements.removeHistoryFile.addEventListener("click", () => {
    elements.historyUploadZone.style.display = "block"
    elements.historyFileDisplay.style.display = "none"
    elements.historyFileInput.value = ""
  })
}

function openHistorySearchModal() {
  tempSelectedCases = JSON.parse(JSON.stringify(selectedHistoryCases))
  elements.historySearchOverlay.classList.add("active")
  elements.historySearchInput.value = ""
  elements.searchResults.style.display = "none"
  updateSelectedCasesPreview()
}

function closeHistorySearchModal() {
  elements.historySearchOverlay.classList.remove("active")
  if (selectedHistoryCases.length === 0) {
    elements.historyCheckbox.checked = false
  }
}

// 存储当前的筛选条件
let currentFilters = {
  caseLibrary: null,
  searchMethod: null
}

function handleSearchInput(e) {
  const value = e.target.value
  if (value.slice(-1) === "/") {
    // 移除输入框中的 "/"
    elements.historySearchInput.value = value.slice(0, -1)
    // 显示筛选面板
    renderFilterPanel()
    elements.filterPanel.classList.add("show")
  } else {
    elements.filterPanel.classList.remove("show")
  }
}

async function renderFilterPanel() {
  // 如果案例库选项还未加载，从API获取
  if (caseLibraryOptions.length === 0) {
    try {
      caseLibraryOptions = await fetchCaseLibraryOptions()
      console.log('[v0] 案例库选项已加载:', caseLibraryOptions)
    } catch (error) {
      console.error('[v0] 加载案例库选项失败:', error)
      // 使用默认选项
      caseLibraryOptions = [
        { value: "all", label: "全量历史用例案例库" },
        { value: "archived", label: "已归档精品案例库" }
      ]
    }
  }
  
  // 渲染案例库选择下拉框
  elements.caseLibrarySelect.innerHTML = caseLibraryOptions.map(opt => 
    `<option value="${opt.value}" ${currentFilters.caseLibrary === opt.value ? 'selected' : ''}>${opt.label}</option>`
  ).join("")
  
  // 渲染搜索方式选择下拉框（这个保持前端固定）
  elements.searchMethodSelect.innerHTML = searchMethodOptions.map(opt => 
    `<option value="${opt.value}" ${currentFilters.searchMethod === opt.value ? 'selected' : ''}>${opt.label}</option>`
  ).join("")
}

function handleFilterConfirm() {
  const caseLibrary = elements.caseLibrarySelect.value
  const searchMethod = elements.searchMethodSelect.value
  
  // 更新筛选条件
  currentFilters.caseLibrary = caseLibrary
  currentFilters.searchMethod = searchMethod
  
  // 渲染筛选标签
  renderFilterTags()
  
  // 关闭筛选面板
  elements.filterPanel.classList.remove("show")
  
  // 聚焦到搜索框
  elements.historySearchInput.focus()
}

function renderFilterTags() {
  const tags = []
  
  if (currentFilters.caseLibrary) {
    const option = caseLibraryOptions.find(opt => opt.value === currentFilters.caseLibrary)
    if (option) {
      tags.push({
        type: 'caseLibrary',
        label: option.label
      })
    }
  }
  
  if (currentFilters.searchMethod) {
    const option = searchMethodOptions.find(opt => opt.value === currentFilters.searchMethod)
    if (option) {
      tags.push({
        type: 'searchMethod',
        label: option.label
      })
    }
  }
  
  elements.filterTags.innerHTML = tags.map(tag => `
    <div class="filter-tag" data-type="${tag.type}">
      <span>${tag.label}</span>
      <button class="filter-tag-remove" data-type="${tag.type}">×</button>
    </div>
  `).join("")
  
  // 绑定删除按钮事件
  elements.filterTags.querySelectorAll('.filter-tag-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation()
      const type = btn.dataset.type
      removeFilterTag(type)
    })
  })
  
  // 更新输入框的左内边距以适应标签宽度
  updateInputPadding()
}

function removeFilterTag(type) {
  currentFilters[type] = null
  renderFilterTags()
}

function updateInputPadding() {
  const tagsWidth = elements.filterTags.offsetWidth
  if (tagsWidth > 0) {
    elements.historySearchInput.style.paddingLeft = `${tagsWidth + 24}px`
  } else {
    elements.historySearchInput.style.paddingLeft = ''
  }
}

async function performHistorySearch() {
  const searchText = elements.historySearchInput.value.trim()
  if (!searchText) {
    showNotification("请输入搜索内容", "error", 2000)
    return
  }
  
  try {
    // 显示加载状态
    elements.searchResultsList.innerHTML = '<div style="text-align:center;padding:40px;color:#7f8c8d;">搜索中...</div>'
    elements.searchResults.style.display = "block"
    
    // 调用后端API进行搜索，传入筛选条件和搜索文本
    const results = await fetchSearchHistoryCases(
      currentFilters.caseLibrary || 'all',
      currentFilters.searchMethod || 'keyword',
      searchText
    )
    
    console.log('[v0] 搜索结果:', results)
    // 存储搜索结果供后续使用
    currentSearchResults = results
    renderSearchResults(results)
  } catch (error) {
    console.error('[v0] 搜索失败:', error)
    showNotification("搜索失败，请检查后端服务是否启动", "error", 3000)
    elements.searchResultsList.innerHTML = '<div class="no-search-results">搜索失败，请检查后端服务是否启动</div>'
  }
}

function renderSearchResults(results) {
  elements.searchResults.style.display = "block"
  
  if (results.length === 0) {
    elements.searchResultsList.innerHTML = '<div class="no-search-results">未找到匹配的用例，您可以上传历史用例文件</div>'
    return
  }
  
  elements.searchResultsList.innerHTML = results.map(tc => {
    const isSelected = tempSelectedCases.some(s => s.id === tc.id)
    return `
      <div class="search-result-item ${isSelected ? "selected" : ""}" data-id="${tc.id}">
        <input type="checkbox" class="search-result-checkbox" ${isSelected ? "checked" : ""}>
        <div class="search-result-info">
          <div class="search-result-name">${tc.name}</div>
          <div class="search-result-id">${tc.id}</div>
        </div>
        <button class="search-result-view" data-id="${tc.id}">查看详情</button>
      </div>
    `
  }).join("")
  
  // 绑定事件
  elements.searchResultsList.querySelectorAll(".search-result-item").forEach(el => {
    const checkbox = el.querySelector(".search-result-checkbox")
    const viewBtn = el.querySelector(".search-result-view")
    const id = el.dataset.id
    
    const toggleSelect = (e) => {
      if (e.target === viewBtn) return
      // 从当前搜索结果中查找，而不是从mock数据
      const tc = currentSearchResults.find(t => t.id === id)
      if (!tc) return
      
      const existingIndex = tempSelectedCases.findIndex(s => s.id === id)
      if (existingIndex >= 0) {
        tempSelectedCases.splice(existingIndex, 1)
        el.classList.remove("selected")
        checkbox.checked = false
      } else {
        tempSelectedCases.push(JSON.parse(JSON.stringify(tc)))
        el.classList.add("selected")
        checkbox.checked = true
        // 需求2：勾选第一个用例时，直接设为模板
        if (tempSelectedCases.length === 1) {
          caseTemplate = JSON.parse(JSON.stringify(tc))
          caseTemplate.id = "TEMPLATE_" + Date.now()
          caseTemplate.name = tc.name + " (模板)"
          savedCaseTemplate = JSON.parse(JSON.stringify(caseTemplate))
          savedTemplateIndex = 0
        }
      }
      updateSelectedCasesPreview()
    }
    
    el.addEventListener("click", toggleSelect)
    
    viewBtn.addEventListener("click", (e) => {
      e.stopPropagation()
      openHistoryCaseDetail(id)
    })
  })
}

function updateSelectedCasesPreview() {
  if (tempSelectedCases.length === 0) {
    elements.selectedCasesSection.style.display = "none"
    elements.templatePreviewSection.style.display = "none"
    return
  }
  
  elements.selectedCasesSection.style.display = "block"
  elements.selectedCasesPreview.innerHTML = tempSelectedCases.map(tc => `
    <div class="selected-preview-item" data-id="${tc.id}">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
      </svg>
      <div class="selected-preview-info">
        <div class="selected-preview-name">${tc.name}</div>
        <div class="selected-preview-id">${tc.id}</div>
      </div>
      <button class="selected-preview-remove" data-id="${tc.id}">移���</button>
    </div>
  `).join("")
  
  elements.selectedCasesPreview.querySelectorAll(".selected-preview-remove").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id
      tempSelectedCases = tempSelectedCases.filter(tc => tc.id !== id)
      updateSelectedCasesPreview()
      const resultItem = elements.searchResultsList.querySelector(`.search-result-item[data-id="${id}"]`)
      if (resultItem) {
        resultItem.classList.remove("selected")
        resultItem.querySelector(".search-result-checkbox").checked = false
      }
    })
  })
  
  // 显示模板预览
  if (savedCaseTemplate) {
    elements.templatePreviewSection.style.display = "block"
    elements.templatePreview.innerHTML = `
      <div class="selected-preview-item template-preview-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <div class="selected-preview-info">
          <div class="selected-preview-name">${savedCaseTemplate.name}</div>
          <div class="selected-preview-id">${savedCaseTemplate.id}</div>
        </div>
        <span class="template-badge">模板</span>
      </div>
    `
  } else {
    elements.templatePreviewSection.style.display = "none"
  }
}

// 只读查看用例详情
function openHistoryCaseDetail(caseId) {
  const tc = mockSearchResults.find(t => t.id === caseId) || tempSelectedCases.find(t => t.id === caseId)
  if (!tc) return
  
  historyCasesForEdit = [JSON.parse(JSON.stringify(tc))]
  currentHistoryCaseIndex = 0
  
  elements.historyCaseDetailOverlay.classList.add("active")
  renderHistoryCaseList()
  renderHistoryCaseDetailReadonly()
}

function closeHistoryCaseDetail() {
  elements.historyCaseDetailOverlay.classList.remove("active")
}

function renderHistoryCaseList() {
  elements.historyCaseList.innerHTML = historyCasesForEdit.map((tc, index) => `
    <div class="case-item ${index === currentHistoryCaseIndex ? "active" : ""}" data-index="${index}">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
      </svg>
      <span>${tc.name}</span>
    </div>
  `).join("")
  
  elements.historyCaseList.querySelectorAll(".case-item").forEach(item => {
    item.addEventListener("click", () => {
      currentHistoryCaseIndex = parseInt(item.dataset.index)
      renderHistoryCaseList()
      renderHistoryCaseDetailReadonly()
    })
  })
}

function renderHistoryCaseDetailReadonly() {
  const tc = historyCasesForEdit[currentHistoryCaseIndex]
  if (!tc) return
  
  elements.historyDetailTitle.textContent = tc.name
  elements.historyDetailId.textContent = `用例 ID: ${tc.id}`
  
  renderHistorySectionReadonly(tc.preconditions, elements.historyPreconditionList, "preconditions")
  renderHistorySectionReadonly(tc.steps, elements.historyStepsList, "steps")
  renderHistorySectionReadonly(tc.expectedResults, elements.historyExpectedResultList, "expectedResults")
}

function renderHistorySectionReadonly(items, container, sectionType) {
  if (!items || items.length === 0) {
    const hintText = sectionType === "preconditions" ? "预置条件" : sectionType === "steps" ? "测试步骤" : "预期结果"
    container.innerHTML = `<p class="empty-hint">暂无${hintText}</p>`
    return
  }

  container.innerHTML = items.map((item, stepIndex) => `
    <div class="step-item" data-step-index="${stepIndex}">
      <div class="step-header">
        <button class="expand-btn readonly-expand-btn ${item.expanded ? "expanded" : ""}" data-section="${sectionType}" data-step-index="${stepIndex}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <span class="step-number">${stepIndex + 1}</span>
        <span class="step-name">${item.name}</span>
      </div>
      <div class="step-content ${item.expanded ? "expanded" : ""}">
        <div class="components-list">
          ${item.components && item.components.length > 0
            ? item.components.map((comp, compIndex) => `
              <div class="component-item">
                <span class="component-number">${compIndex + 1}</span>
                <div class="component-info">
                  <div class="component-name">${comp.name}</div>
                  <pre class="component-params">${JSON.stringify(comp.params, null, 2)}</pre>
                </div>
              </div>
            `).join("")
            : '<p class="empty-hint" style="font-size: 12px; padding: 8px;">暂无组件</p>'
          }
        </div>
      </div>
    </div>
  `).join("")

  // 绑定展开/折叠
  container.querySelectorAll(".readonly-expand-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = parseInt(btn.dataset.stepIndex)
      historyCasesForEdit[currentHistoryCaseIndex][sectionType][stepIndex].expanded = 
        !historyCasesForEdit[currentHistoryCaseIndex][sectionType][stepIndex].expanded
      renderHistoryCaseDetailReadonly()
    })
  })
}

function copyToClipboard(text, successMsg) {
  navigator.clipboard.writeText(text).then(() => {
    showNotification(successMsg || "已复制到剪贴板", "success", 2000)
  }).catch(() => {
    const textarea = document.createElement("textarea")
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand("copy")
    document.body.removeChild(textarea)
    showNotification(successMsg || "已复制到剪贴板", "success", 2000)
  })
}

function saveHistorySelection() {
  selectedHistoryCases = JSON.parse(JSON.stringify(tempSelectedCases))
  
  if (selectedHistoryCases.length > 0 || elements.historyFileDisplay.style.display === "flex") {
    elements.selectedHistoryCases.style.display = "block"
    renderSelectedCasesList()
  } else {
    elements.selectedHistoryCases.style.display = "none"
  }
  
  closeHistorySearchModal()
}

function renderSelectedCasesList() {
  let html = ""
  
  // 优先显示上传的文件
  if (elements.historyFileDisplay.style.display === "flex") {
    html += `
      <div class="selected-case-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <span class="selected-case-name">${elements.historyFileName.textContent} (上传文件)</span>
      </div>
    `
  } else if (savedCaseTemplate) {
    // 其次显示保存的模板
    html += `
      <div class="selected-case-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <span class="selected-case-name">${savedCaseTemplate.name}</span>
      </div>
    `
  }
  
  elements.selectedCasesList.innerHTML = html
}

function displaySavedResult() {
  // 显示最外层的已选择用例区域
  if (elements.historyFileDisplay.style.display === "flex" || savedCaseTemplate) {
    elements.selectedHistoryCases.style.display = "block"
    renderSelectedCasesList()
  } else {
    elements.selectedHistoryCases.style.display = "none"
  }
}

// ============ 历史用例编辑弹窗相关 ============

let templateCaseIndex = 0  // 当前选择的模板用例索引
let currentEditCaseIndex = 0  // 当前查看的用例索引
let isViewingTemplate = false  // 当前是否在查看模板

function initHistoryCaseEditElements() {
  elements.historyCaseEditOverlay = document.getElementById("historyCaseEditOverlay")
  elements.closeHistoryCaseEditBtn = document.getElementById("closeHistoryCaseEditBtn")
  elements.cancelHistoryCaseEditBtn = document.getElementById("cancelHistoryCaseEditBtn")
  elements.saveHistoryCaseEditBtn = document.getElementById("saveHistoryCaseEditBtn")
  elements.historyEditCaseList = document.getElementById("historyEditCaseList")
  elements.templateCaseDisplay = document.getElementById("templateCaseDisplay")
  elements.historyEditDetailPanel = document.getElementById("historyEditDetailPanel")
  elements.historyEditDetailTitle = document.getElementById("historyEditDetailTitle")
  elements.historyEditDetailId = document.getElementById("historyEditDetailId")
  elements.historyEditPreconditionList = document.getElementById("historyEditPreconditionList")
  elements.historyEditStepsList = document.getElementById("historyEditStepsList")
  elements.historyEditExpectedResultList = document.getElementById("historyEditExpectedResultList")
  elements.addHistoryEditPreconditionBtn = document.getElementById("addHistoryEditPreconditionBtn")
  elements.addHistoryEditStepBtn = document.getElementById("addHistoryEditStepBtn")
  elements.addHistoryEditExpectedResultBtn = document.getElementById("addHistoryEditExpectedResultBtn")
  elements.templateCheckboxLabel = document.getElementById("templateCheckboxLabel")
  elements.setAsTemplateCheckbox = document.getElementById("setAsTemplateCheckbox")
  elements.copyPreconditionsBtn = document.getElementById("copyPreconditionsBtn")
  elements.copyStepsBtn = document.getElementById("copyStepsBtn")
  elements.copyExpectedResultsBtn = document.getElementById("copyExpectedResultsBtn")
  elements.editSelectedCasesBtn = document.getElementById("editSelectedCasesBtn")
  
  // JSON导入
  elements.stepImportJsonInput = document.getElementById("stepImportJsonInput")
  elements.importStepJsonBtn = document.getElementById("importStepJsonBtn")
  elements.componentImportJsonInput = document.getElementById("componentImportJsonInput")
  elements.importComponentJsonBtn = document.getElementById("importComponentJsonBtn")
  
  // 模板预览和用例名称编辑
  elements.templatePreviewSection = document.getElementById("templatePreviewSection")
  elements.templatePreview = document.getElementById("templatePreview")
  elements.historyEditCaseNameInput = document.getElementById("historyEditCaseNameInput")
  elements.editCaseNameBtn = document.getElementById("editCaseNameBtn")
  elements.saveCaseNameBtn = document.getElementById("saveCaseNameBtn")
}

function bindHistoryCaseEditEvents() {
  // 编辑已选用例按钮
  if (elements.editSelectedCasesBtn) {
    elements.editSelectedCasesBtn.addEventListener("click", openHistoryCaseEditModal)
  }
  
  // 关闭编辑弹窗
  elements.closeHistoryCaseEditBtn.addEventListener("click", closeHistoryCaseEditModal)
  elements.cancelHistoryCaseEditBtn.addEventListener("click", closeHistoryCaseEditModal)
  elements.historyCaseEditOverlay.addEventListener("click", (e) => {
    if (e.target === elements.historyCaseEditOverlay) closeHistoryCaseEditModal()
  })
  
  // 保存编辑
  elements.saveHistoryCaseEditBtn.addEventListener("click", saveHistoryCaseEdit)
  
  // 模板复选框
  elements.setAsTemplateCheckbox.addEventListener("change", handleSetAsTemplate)
  
  // 添加按钮（仅模板模式可用）
  elements.addHistoryEditPreconditionBtn.addEventListener("click", () => {
    if (isViewingTemplate) openStepEditForHistoryEdit(null, "preconditions")
  })
  elements.addHistoryEditStepBtn.addEventListener("click", () => {
    if (isViewingTemplate) openStepEditForHistoryEdit(null, "steps")
  })
  elements.addHistoryEditExpectedResultBtn.addEventListener("click", () => {
    if (isViewingTemplate) openStepEditForHistoryEdit(null, "expectedResults")
  })
  
  // 复制整个section按钮
  elements.copyPreconditionsBtn.addEventListener("click", () => copySectionToClipboard("preconditions"))
  elements.copyStepsBtn.addEventListener("click", () => copySectionToClipboard("steps"))
  elements.copyExpectedResultsBtn.addEventListener("click", () => copySectionToClipboard("expectedResults"))
  
  // JSON导入按钮
  elements.importStepJsonBtn.addEventListener("click", importStepFromJson)
  elements.importComponentJsonBtn.addEventListener("click", importComponentFromJson)
  
  // 用例名称编辑
  elements.editCaseNameBtn.addEventListener("click", startEditingCaseName)
  elements.saveCaseNameBtn.addEventListener("click", saveCaseName)
  elements.historyEditCaseNameInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveCaseName()
    if (e.key === "Escape") cancelEditingCaseName()
  })
}

function openHistoryCaseEditModal() {
  if (tempSelectedCases.length === 0) {
    showNotification("请先选择用例", "error", 2000)
    return
  }
  
  // 复制数据用于编辑
  historyCasesForEdit = JSON.parse(JSON.stringify(tempSelectedCases))
  historyCasesBackup = JSON.parse(JSON.stringify(historyCasesForEdit))
  
  // 如果有已保存的模板和索引，使用它们；否���默认第一个
  if (savedCaseTemplate && savedTemplateIndex !== null && savedTemplateIndex < historyCasesForEdit.length) {
    templateCaseIndex = savedTemplateIndex
    caseTemplate = JSON.parse(JSON.stringify(savedCaseTemplate))
  } else {
    templateCaseIndex = 0
    caseTemplate = JSON.parse(JSON.stringify(historyCasesForEdit[0]))
    caseTemplate.id = "TEMPLATE_" + Date.now()
    caseTemplate.name = caseTemplate.name + " (模板)"
  }
  
  // 需求3：默认选择用例模板进行展示
  currentEditCaseIndex = templateCaseIndex
  isViewingTemplate = true
  
  elements.historyCaseEditOverlay.classList.add("active")
  renderHistoryEditCaseList()
  renderHistoryEditDetail()
}

function closeHistoryCaseEditModal() {
  elements.historyCaseEditOverlay.classList.remove("active")
  caseTemplate = null
}

function saveHistoryCaseEdit() {
  // 只保存模板，不更新历史用例
  if (caseTemplate) {
    savedCaseTemplate = JSON.parse(JSON.stringify(caseTemplate))
    savedTemplateIndex = templateCaseIndex
  }
  
  // 关键修复：不覆盖tempSelectedCases，保持原始历史用例不变
  // 只需要关闭编辑弹窗
  historyCasesBackup = null
  elements.historyCaseEditOverlay.classList.remove("active")
  
  // 更新搜索弹窗中的已选用例预览
  updateSelectedCasesPreview()
  
  // 在外层显示保存结果
  displaySavedResult()
}

function renderHistoryEditCaseList() {
  // 渲染已选用例列表
  elements.historyEditCaseList.innerHTML = historyCasesForEdit.map((tc, index) => `
    <div class="case-item-with-actions ${!isViewingTemplate && index === currentEditCaseIndex ? "active" : ""}" data-index="${index}">
      <div class="case-item-info">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <span>${tc.name}</span>
      </div>
      ${index === templateCaseIndex ? '<span class="template-badge">模板</span>' : ''}
    </div>
  `).join("")
  
  // 绑定点���事���
  elements.historyEditCaseList.querySelectorAll(".case-item-with-actions").forEach(item => {
    item.addEventListener("click", () => {
      currentEditCaseIndex = parseInt(item.dataset.index)
      isViewingTemplate = false
      renderHistoryEditCaseList()
      renderHistoryEditDetail()
    })
  })
  
  // 渲染模板显示
  renderTemplateDisplay()
}

function renderTemplateDisplay() {
  if (!caseTemplate) {
    elements.templateCaseDisplay.innerHTML = '<div class="template-hint">暂无模板</div>'
    return
  }
  
  elements.templateCaseDisplay.innerHTML = `
    <div class="case-item ${isViewingTemplate ? "active" : ""}">
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
      </svg>
      <span>${caseTemplate.name}</span>
    </div>
  `
  
  elements.templateCaseDisplay.querySelector(".case-item").addEventListener("click", () => {
    isViewingTemplate = true
    renderHistoryEditCaseList()
    renderHistoryEditDetail()
  })
}

function renderHistoryEditDetail() {
  let tc
  if (isViewingTemplate) {
    tc = caseTemplate
  } else {
    tc = historyCasesForEdit[currentEditCaseIndex]
  }
  
  if (!tc) return
  
  elements.historyEditDetailTitle.textContent = tc.name
  elements.historyEditDetailId.textContent = `用例 ID: ${tc.id}`
  
  // 显示/隐藏用例名称编辑按钮（仅在查看模板时显示）
  elements.editCaseNameBtn.style.display = isViewingTemplate ? "inline-flex" : "none"
  elements.historyEditCaseNameInput.style.display = "none"
  elements.saveCaseNameBtn.style.display = "none"
  
  // 显示/隐藏设为模板复选框（仅在查看已选用例时显示）
  elements.templateCheckboxLabel.style.display = isViewingTemplate ? "none" : "flex"
  elements.setAsTemplateCheckbox.checked = currentEditCaseIndex === templateCaseIndex
  
  // 显示/隐藏添加按钮（仅在模板模式显示）
  const showAddBtns = isViewingTemplate ? "inline-flex" : "none"
  elements.addHistoryEditPreconditionBtn.style.display = showAddBtns
  elements.addHistoryEditStepBtn.style.display = showAddBtns
  elements.addHistoryEditExpectedResultBtn.style.display = showAddBtns
  
  // 隐藏section级别的复制按钮
  elements.copyPreconditionsBtn.style.display = "none"
  elements.copyStepsBtn.style.display = "none"
  elements.copyExpectedResultsBtn.style.display = "none"
  
  if (isViewingTemplate) {
    // 模板模式：可编辑，复制按钮是复制步骤/组件
    renderHistoryEditSectionEditable(tc.preconditions, elements.historyEditPreconditionList, "preconditions")
    renderHistoryEditSectionEditable(tc.steps, elements.historyEditStepsList, "steps")
    renderHistoryEditSectionEditable(tc.expectedResults, elements.historyEditExpectedResultList, "expectedResults")
  } else {
    // 只读模式：带复制到剪贴板的按钮
    renderHistoryEditSectionReadonly(tc.preconditions, elements.historyEditPreconditionList, "preconditions")
    renderHistoryEditSectionReadonly(tc.steps, elements.historyEditStepsList, "steps")
    renderHistoryEditSectionReadonly(tc.expectedResults, elements.historyEditExpectedResultList, "expectedResults")
  }
}

function renderHistoryEditSectionReadonly(items, container, sectionType) {
  if (!items || items.length === 0) {
    const hintText = sectionType === "preconditions" ? "预置条件" : sectionType === "steps" ? "测试步骤" : "预期结果"
    container.innerHTML = `<p class="empty-hint">暂无${hintText}</p>`
    return
  }

  container.innerHTML = items.map((item, stepIndex) => `
    <div class="step-item" data-step-index="${stepIndex}">
      <div class="step-header">
        <button class="expand-btn edit-expand-btn ${item.expanded ? "expanded" : ""}" data-section="${sectionType}" data-step-index="${stepIndex}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <span class="step-number">${stepIndex + 1}</span>
        <span class="step-name">${item.name}</span>
        <div class="step-actions">
          <button class="icon-btn copy-step-json-btn" data-section="${sectionType}" data-step-index="${stepIndex}" title="复制步骤JSON">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          </button>
        </div>
      </div>
      <div class="step-content ${item.expanded ? "expanded" : ""}">
        <div class="components-list">
          ${item.components && item.components.length > 0
            ? item.components.map((comp, compIndex) => `
              <div class="component-item">
                <span class="component-number">${compIndex + 1}</span>
                <div class="component-info">
                  <div class="component-name">${comp.name}</div>
                  <pre class="component-params">${JSON.stringify(comp.params, null, 2)}</pre>
                </div>
                <div class="component-actions">
                  <button class="icon-btn copy-comp-json-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="复制组件JSON">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                  </button>
                </div>
              </div>
            `).join("")
            : '<p class="empty-hint" style="font-size: 12px; padding: 8px;">暂无组件</p>'
          }
        </div>
      </div>
    </div>
  `).join("")

  bindReadonlySectionEvents(container, sectionType)
}

function renderHistoryEditSectionEditable(items, container, sectionType) {
  if (!items || items.length === 0) {
    const hintText = sectionType === "preconditions" ? "预置条件" : sectionType === "steps" ? "测试步骤" : "预期结果"
    container.innerHTML = `<p class="empty-hint">暂无${hintText}，点击上方按钮添加</p>`
    return
  }

  container.innerHTML = items.map((item, stepIndex) => `
    <div class="step-item" draggable="true" data-type="${sectionType}" data-section="${sectionType}" data-step-index="${stepIndex}">
      <div class="step-header">
        <div class="drag-handle">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="9" cy="5" r="1"></circle>
            <circle cx="9" cy="12" r="1"></circle>
            <circle cx="9" cy="19" r="1"></circle>
            <circle cx="15" cy="5" r="1"></circle>
            <circle cx="15" cy="12" r="1"></circle>
            <circle cx="15" cy="19" r="1"></circle>
          </svg>
        </div>
        <button class="expand-btn edit-expand-btn ${item.expanded ? "expanded" : ""}" data-section="${sectionType}" data-step-index="${stepIndex}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <span class="step-number">${stepIndex + 1}</span>
        <span class="step-name">${item.name}</span>
        <div class="step-actions">
          <button class="icon-btn duplicate-step-btn" data-section="${sectionType}" data-step-index="${stepIndex}" title="复制步骤">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          </button>
          <button class="icon-btn edit-step-btn" data-section="${sectionType}" data-step-index="${stepIndex}" title="编辑">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="icon-btn danger delete-step-btn" data-section="${sectionType}" data-step-index="${stepIndex}" title="删除">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>
      <div class="step-content ${item.expanded ? "expanded" : ""}">
        <div class="components-list">
          ${item.components && item.components.length > 0
            ? item.components.map((comp, compIndex) => `
              <div class="component-item" draggable="true" data-type="component" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}">
                <div class="drag-handle">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="9" cy="5" r="1"></circle>
                    <circle cx="9" cy="12" r="1"></circle>
                    <circle cx="9" cy="19" r="1"></circle>
                    <circle cx="15" cy="5" r="1"></circle>
                    <circle cx="15" cy="12" r="1"></circle>
                    <circle cx="15" cy="19" r="1"></circle>
                  </svg>
                </div>
                <span class="component-number">${compIndex + 1}</span>
                <div class="component-info">
                  <div class="component-name">${comp.name}</div>
                  <pre class="component-params">${JSON.stringify(comp.params, null, 2)}</pre>
                </div>
                <div class="component-actions">
                  <button class="icon-btn duplicate-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="复制组件">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                  </button>
                  <button class="icon-btn edit-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="编辑">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>
                  <button class="icon-btn danger delete-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="删除">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              </div>
            `).join("")
            : '<p class="empty-hint" style="font-size: 12px; padding: 8px;">暂无组件</p>'
          }
        </div>
        <button class="add-btn add-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}">+ 添加组件</button>
      </div>
    </div>
  `).join("")

  bindEditableSectionEvents(container, sectionType)
}

function bindReadonlySectionEvents(container, sectionType) {
  // 展开/折叠
  container.querySelectorAll(".edit-expand-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = parseInt(btn.dataset.stepIndex)
      historyCasesForEdit[currentEditCaseIndex][sectionType][stepIndex].expanded = 
        !historyCasesForEdit[currentEditCaseIndex][sectionType][stepIndex].expanded
      renderHistoryEditDetail()
    })
  })

  // 复制步骤JSON到剪贴板
  container.querySelectorAll(".copy-step-json-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = parseInt(btn.dataset.stepIndex)
      const step = historyCasesForEdit[currentEditCaseIndex][sectionType][stepIndex]
      copyToClipboard(JSON.stringify(step, null, 2), "步骤已复制到剪贴板")
    })
  })

  // 复制组件JSON到剪贴板
  container.querySelectorAll(".copy-comp-json-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = parseInt(btn.dataset.stepIndex)
      const compIndex = parseInt(btn.dataset.compIndex)
      const comp = historyCasesForEdit[currentEditCaseIndex][sectionType][stepIndex].components[compIndex]
      copyToClipboard(JSON.stringify(comp, null, 2), "组件已复制到剪贴板")
    })
  })
}

function bindEditableSectionEvents(container, sectionType) {
  // 拖动排序
  let draggedElement = null
  let draggedType = null
  let draggedSection = null
  let draggedStepIndex = null
  let draggedCompIndex = null
  
  container.querySelectorAll('[draggable="true"]').forEach(item => {
    item.addEventListener("dragstart", (e) => {
      e.stopPropagation()
      draggedElement = e.target.closest('[draggable="true"]')
      draggedType = draggedElement.dataset.type
      draggedSection = draggedElement.dataset.section
      draggedStepIndex = draggedElement.dataset.stepIndex ? parseInt(draggedElement.dataset.stepIndex) : null
      draggedCompIndex = draggedElement.dataset.compIndex ? parseInt(draggedElement.dataset.compIndex) : null
      
      draggedElement.style.opacity = "0.5"
    })
    
    item.addEventListener("dragend", (e) => {
      if (draggedElement) {
        draggedElement.style.opacity = ""
      }
      container.querySelectorAll(".drag-over").forEach(el => el.classList.remove("drag-over"))
    })
    
    item.addEventListener("dragover", (e) => {
      e.preventDefault()
      e.stopPropagation()
    })
    
    item.addEventListener("dragenter", (e) => {
      e.preventDefault()
      e.stopPropagation()
      const dropTarget = e.target.closest('[draggable="true"]')
      if (dropTarget && dropTarget !== draggedElement) {
        dropTarget.classList.add("drag-over")
      }
    })
    
    item.addEventListener("dragleave", (e) => {
      e.stopPropagation()
      const dropTarget = e.target.closest('[draggable="true"]')
      if (dropTarget) {
        dropTarget.classList.remove("drag-over")
      }
    })
    
    item.addEventListener("drop", (e) => {
      e.preventDefault()
      e.stopPropagation()
      
      if (!draggedElement) return
      
      const dropTarget = e.target.closest('[draggable="true"]')
      if (!dropTarget || dropTarget === draggedElement) return
      
      const dropType = dropTarget.dataset.type
      const dropSection = dropTarget.dataset.section
      const dropStepIndex = dropTarget.dataset.stepIndex ? parseInt(dropTarget.dataset.stepIndex) : null
      const dropCompIndex = dropTarget.dataset.compIndex ? parseInt(dropTarget.dataset.compIndex) : null
      
      // 步骤拖动
      if (draggedType !== "component" && dropType !== "component") {
        if (draggedSection === dropSection) {
          const items = caseTemplate[draggedSection]
          const [removed] = items.splice(draggedStepIndex, 1)
          const newIndex = draggedStepIndex < dropStepIndex ? dropStepIndex - 1 : dropStepIndex
          items.splice(newIndex, 0, removed)
          renderHistoryEditDetail()
        }
      }
      // 组件拖动
      else if (draggedType === "component" && dropType === "component") {
        if (draggedSection === dropSection && draggedStepIndex === dropStepIndex) {
          const components = caseTemplate[draggedSection][draggedStepIndex].components
          const [removed] = components.splice(draggedCompIndex, 1)
          const newIndex = draggedCompIndex < dropCompIndex ? dropCompIndex - 1 : dropCompIndex
          components.splice(newIndex, 0, removed)
          renderHistoryEditDetail()
        }
      }
      
      dropTarget.classList.remove("drag-over")
    })
  })
  
  // 展开/折叠
  container.querySelectorAll(".edit-expand-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = parseInt(btn.dataset.stepIndex)
      caseTemplate[sectionType][stepIndex].expanded = !caseTemplate[sectionType][stepIndex].expanded
      renderHistoryEditDetail()
    })
  })

  // 复制步骤（复制一份相同的）
  container.querySelectorAll(".duplicate-step-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = parseInt(btn.dataset.stepIndex)
      const originalStep = caseTemplate[sectionType][stepIndex]
      const duplicatedStep = JSON.parse(JSON.stringify(originalStep))
      duplicatedStep.id = "item" + Date.now()
      caseTemplate[sectionType].splice(stepIndex + 1, 0, duplicatedStep)
      renderHistoryEditDetail()
    })
  })

  // 编辑步骤
  container.querySelectorAll(".edit-step-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      openStepEditForHistoryEdit(parseInt(btn.dataset.stepIndex), btn.dataset.section)
    })
  })

  // 删除步骤
  container.querySelectorAll(".delete-step-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation()
      const confirmed = await showConfirmDialog("确定要删除此步骤吗？", "删����认")
      if (confirmed) {
        const stepIndex = parseInt(btn.dataset.stepIndex)
        caseTemplate[sectionType].splice(stepIndex, 1)
        renderHistoryEditDetail()
      }
    })
  })

  // 添加组件
  container.querySelectorAll(".add-comp-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      openComponentEditForHistoryEdit(parseInt(btn.dataset.stepIndex), null, btn.dataset.section)
    })
  })

  // 复制组件（复制一份相同的）
  container.querySelectorAll(".duplicate-comp-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      const stepIndex = parseInt(btn.dataset.stepIndex)
      const compIndex = parseInt(btn.dataset.compIndex)
      const originalComp = caseTemplate[sectionType][stepIndex].components[compIndex]
      const duplicatedComp = JSON.parse(JSON.stringify(originalComp))
      duplicatedComp.id = "c" + Date.now()
      caseTemplate[sectionType][stepIndex].components.splice(compIndex + 1, 0, duplicatedComp)
      renderHistoryEditDetail()
    })
  })

  // 编辑组件
  container.querySelectorAll(".edit-comp-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      openComponentEditForHistoryEdit(parseInt(btn.dataset.stepIndex), parseInt(btn.dataset.compIndex), btn.dataset.section)
    })
  })

  // 删除组件
  container.querySelectorAll(".delete-comp-btn").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation()
      const confirmed = await showConfirmDialog("确定要删除此组件吗？", "删除确认")
      if (confirmed) {
        const stepIndex = parseInt(btn.dataset.stepIndex)
        const compIndex = parseInt(btn.dataset.compIndex)
        caseTemplate[sectionType][stepIndex].components.splice(compIndex, 1)
        renderHistoryEditDetail()
      }
    })
  })
}

function handleSetAsTemplate() {
  if (elements.setAsTemplateCheckbox.checked) {
    templateCaseIndex = currentEditCaseIndex
    // 复制选中的用例作为模板
    caseTemplate = JSON.parse(JSON.stringify(historyCasesForEdit[currentEditCaseIndex]))
    caseTemplate.id = "TEMPLATE_" + Date.now()
    caseTemplate.name = caseTemplate.name + " (模板)"
    renderHistoryEditCaseList()
    renderTemplateDisplay()
  }
}

// 用例名称编辑功能
function startEditingCaseName() {
  if (!isViewingTemplate || !caseTemplate) return
  
  elements.historyEditDetailTitle.style.display = "none"
  elements.historyEditCaseNameInput.style.display = "block"
  elements.historyEditCaseNameInput.value = caseTemplate.name
  elements.editCaseNameBtn.style.display = "none"
  elements.saveCaseNameBtn.style.display = "inline-flex"
  elements.historyEditCaseNameInput.focus()
}

function saveCaseName() {
  const newName = elements.historyEditCaseNameInput.value.trim()
  if (!newName) {
    showNotification("请输入用例名称", "error", 2000)
    return
  }
  
  if (caseTemplate) {
    caseTemplate.name = newName
    // 需求4：同时更新savedCaseTemplate，确保修改被保存
    savedCaseTemplate = JSON.parse(JSON.stringify(caseTemplate))
  }
  
  cancelEditingCaseName()
  renderHistoryEditDetail()
  renderTemplateDisplay()
}

function cancelEditingCaseName() {
  elements.historyEditDetailTitle.style.display = "block"
  elements.historyEditCaseNameInput.style.display = "none"
  elements.editCaseNameBtn.style.display = "inline-flex"
  elements.saveCaseNameBtn.style.display = "none"
}

function copySectionToClipboard(sectionType) {
  const tc = historyCasesForEdit[currentEditCaseIndex]
  if (!tc || !tc[sectionType] || tc[sectionType].length === 0) {
    showNotification("当前section为空，无法复制", "warning", 2000)
    return
  }
  copyToClipboard(JSON.stringify(tc[sectionType], null, 2), "已复制到剪贴板")
}

// 模板编辑 - 步骤编辑
function openStepEditForHistoryEdit(stepIndex, section) {
  editingStepIndex = stepIndex
  editingSection = section
  selectedPresetStep = null
  isEditingHistoryCase = true

  const titleMap = {
    preconditions: stepIndex !== null ? "编辑预置条件" : "添加预置条件",
    steps: stepIndex !== null ? "编辑测试步骤" : "添加测试步骤",
    expectedResults: stepIndex !== null ? "编辑预期结果" : "添加预期结果",
  }

  elements.stepEditTitle.textContent = titleMap[section]
  elements.stepImportJsonInput.value = ""

  if (stepIndex !== null) {
    const item = caseTemplate[section][stepIndex]
    elements.stepNameInput.value = item.name
    elements.stepDescInput.value = item.description || ""
  } else {
    elements.stepNameInput.value = ""
    elements.stepDescInput.value = ""
  }

  // 需求2：渲染预置步骤的下拉选择
  renderPresetStepsDropdown()
  
  elements.saveStepBtn.onclick = saveStepForHistoryEdit
  elements.stepEditOverlay.classList.add("active")
}

// 渲染预置步骤下拉菜单
function renderPresetStepsDropdown() {
  const dropdown = elements.stepNameDropdown
  dropdown.innerHTML = presetSteps.map(step => `
    <div class="select-option" data-preset-id="${step.id}">
      <div class="select-option-name">${step.name}</div>
      ${step.description ? `<div class="select-option-desc">${step.description}</div>` : ''}
      ${step.components && step.components.length > 0 ? `<div class="select-option-components">包含 ${step.components.length} 个组件</div>` : ''}
    </div>
  `).join('')
  
  // 搜索和过滤功能
  elements.stepNameInput.addEventListener("input", (e) => {
    const searchText = e.target.value.toLowerCase()
    const options = dropdown.querySelectorAll(".select-option")
    options.forEach(opt => {
      const name = opt.querySelector('.select-option-name').textContent.toLowerCase()
      const desc = opt.querySelector('.select-option-desc')?.textContent.toLowerCase() || ""
      opt.style.display = (name.includes(searchText) || desc.includes(searchText)) ? "block" : "none"
    })
  })
  
  // 显示/隐藏下拉框
  elements.stepNameInput.addEventListener("focus", () => {
    dropdown.classList.add("show")
  })
  
  elements.stepNameInput.addEventListener("blur", () => {
    setTimeout(() => {
      dropdown.classList.remove("show")
    }, 200)
  })
  
  // 选择预置步骤
  dropdown.querySelectorAll(".select-option").forEach(opt => {
    opt.addEventListener("click", () => {
      const presetId = opt.dataset.presetId
      const preset = presetSteps.find(s => s.id === presetId)
      if (preset) {
        elements.stepNameInput.value = preset.name
        elements.stepDescInput.value = preset.description || ""
        selectedPresetStep = preset
        dropdown.classList.remove("show")
      }
    })
  })
}

function saveStepForHistoryEdit() {
  const name = elements.stepNameInput.value.trim()
  if (!name) {
    showNotification("请输入名称", "error", 2000)
    return
  }

  if (editingStepIndex !== null) {
    caseTemplate[editingSection][editingStepIndex].name = name
    caseTemplate[editingSection][editingStepIndex].description = elements.stepDescInput.value.trim()
  } else {
    let components = []
    if (selectedPresetStep && selectedPresetStep.components) {
      components = selectedPresetStep.components.map((comp, index) => ({
        id: "c" + Date.now() + "_" + index,
        type: comp.type,
        name: comp.name,
        params: JSON.parse(JSON.stringify(comp.params)),
      }))
    }

    const newItem = {
      id: "item" + Date.now(),
      name: name,
      description: elements.stepDescInput.value.trim(),
      expanded: true,
      components: components,
    }
    caseTemplate[editingSection].push(newItem)
  }

  closeStepEdit()
  renderHistoryEditDetail()
  showNotification("步骤保存成功", "success", 2000)
}

// 模板编辑 - 组件编辑
function openComponentEditForHistoryEdit(stepIndex, compIndex, section) {
  editingStepIndex = stepIndex
  editingComponentIndex = compIndex
  editingSection = section
  selectedPresetComponent = null
  isEditingHistoryCase = true

  elements.componentImportJsonInput.value = ""

  if (compIndex !== null) {
    const comp = caseTemplate[section][stepIndex].components[compIndex]
    elements.componentEditTitle.textContent = "编辑组件"
    const presetComp = presetComponents.find(p => p.type === comp.type)
    elements.componentTypeSelect.value = presetComp ? presetComp.name : comp.type
    elements.componentNameInput.value = comp.name
    elements.componentParamsInput.value = JSON.stringify(comp.params, null, 2)
    // 更新参数摘要显示
    updateParamSummary(comp.params)
  } else {
    elements.componentEditTitle.textContent = "添加组件"
    elements.componentTypeSelect.value = ""
    elements.componentNameInput.value = ""
    elements.componentParamsInput.value = "{}"
    // 清空���数���要显示
    updateParamSummary({})
  }

  // 需求2：渲染预置组件的下拉选择
  renderPresetComponentsDropdown()
  
  elements.saveComponentBtn.onclick = saveComponentForHistoryEdit
  elements.componentEditOverlay.classList.add("active")
}

// 渲染预置组件下拉菜单
function renderPresetComponentsDropdown() {
  const dropdown = elements.componentNameDropdown
  dropdown.innerHTML = presetComponents.map(comp => `
    <div class="select-option" data-preset-id="${comp.id}">
      <div class="select-option-name">${comp.name}</div>
      ${comp.description ? `<div class="select-option-desc">${comp.description}</div>` : ''}
      ${comp.type ? `<div class="select-option-desc">类型: ${comp.type}${comp.alias ? ' | 别名: ' + comp.alias : ''}</div>` : ''}
    </div>
  `).join('')
  
  // 清除之前的事件监听器，使用新的克隆元素替���旧元素
  const oldTypeSelect = elements.componentTypeSelect
  const newTypeSelect = oldTypeSelect.cloneNode(true)
  oldTypeSelect.parentNode.replaceChild(newTypeSelect, oldTypeSelect)
  elements.componentTypeSelect = newTypeSelect
  
  // 搜索和过滤功能
  elements.componentTypeSelect.addEventListener("input", (e) => {
    const searchText = e.target.value.toLowerCase()
    const options = dropdown.querySelectorAll(".select-option")
    options.forEach(opt => {
      const name = opt.querySelector('.select-option-name').textContent.toLowerCase()
      const descs = opt.querySelectorAll('.select-option-desc')
      let descText = ''
      descs.forEach(d => descText += d.textContent.toLowerCase() + ' ')
      opt.style.display = (name.includes(searchText) || descText.includes(searchText)) ? "block" : "none"
    })
  })
  
  // 显示/隐藏下拉框
  elements.componentTypeSelect.addEventListener("focus", () => {
    dropdown.classList.add("show")
  })
  
  // 使用mousedown阻止blur事件触发
  dropdown.addEventListener("mousedown", (e) => {
    e.preventDefault() // 阻止input失去焦点
  })
  
  elements.componentTypeSelect.addEventListener("blur", () => {
    setTimeout(() => {
      dropdown.classList.remove("show")
    }, 150)
  })
  
  // 选择预置组件 - 使用事件委托
  dropdown.addEventListener("click", function(e) {
    const opt = e.target.closest('.select-option')
    if (!opt) return
    
    const presetId = opt.dataset.presetId
    const preset = presetComponents.find(c => c.id === presetId)
    
    if (preset) {
      elements.componentTypeSelect.value = preset.name
      elements.componentNameInput.value = preset.description || preset.name
      // 使用componentDefaultParams获取默认参数
      const defaultParams = componentDefaultParams[preset.type] || {}
      elements.componentParamsInput.value = JSON.stringify(defaultParams, null, 2)
      // 更新参数摘要显示
      updateParamSummary(defaultParams)
      selectedPresetComponent = preset
      dropdown.classList.remove("show")
      // 让input失去焦点
      elements.componentTypeSelect.blur()
    }
  })
}

function saveComponentForHistoryEdit() {
  const funcDesc = elements.componentNameInput.value.trim()
  if (!funcDesc) {
    showNotification("请输入组件功能描述", "error", 2000)
    return
  }

  const compNameValue = elements.componentTypeSelect.value.trim()
  if (!compNameValue) {
    showNotification("请选择组件名称", "error", 2000)
    return
  }

  let compType = "input"
  const presetComp = presetComponents.find(p => p.name === compNameValue)
  if (presetComp) {
    compType = presetComp.type
  } else if (selectedPresetComponent) {
    compType = selectedPresetComponent.type
  }

  let params
  try {
    params = JSON.parse(elements.componentParamsInput.value)
  } catch (e) {
    showNotification("参数格式错误，请输入有效的 JSON", "error", 2000)
    return
  }

  // 确保目标步骤存在components数组
  if (!caseTemplate[editingSection][editingStepIndex].components) {
    caseTemplate[editingSection][editingStepIndex].components = []
  }

  if (editingComponentIndex !== null) {
    caseTemplate[editingSection][editingStepIndex].components[editingComponentIndex] = {
      ...caseTemplate[editingSection][editingStepIndex].components[editingComponentIndex],
      type: compType,
      name: funcDesc,
      params,
    }
  } else {
    const newComp = {
      id: "c" + Date.now(),
      type: compType,
      name: funcDesc,
      params,
    }
    caseTemplate[editingSection][editingStepIndex].components.push(newComp)
  }

  closeComponentEdit()
  renderHistoryEditDetail()
  showNotification("组件保存成功", "success", 2000)
}

// JSON导入功能
function importStepFromJson() {
  const jsonStr = elements.stepImportJsonInput.value.trim()
  if (!jsonStr) {
    showNotification("请输入JSON", "error", 2000)
    return
  }
  
  try {
    const step = JSON.parse(jsonStr)
    if (step.name) {
      elements.stepNameInput.value = step.name
    }
    if (step.description) {
      elements.stepDescInput.value = step.description
    }
    // 如���有组件，保存以便后续使用
    if (step.components && step.components.length > 0) {
      selectedPresetStep = step
    }
    showNotification("导入成功，请检查并保存", "success", 2000)
  } catch (e) {
    showNotification("JSON格式错误：" + e.message, "error", 2000)
  }
}

function importComponentFromJson() {
  const jsonStr = elements.componentImportJsonInput.value.trim()
  if (!jsonStr) {
    showNotification("请输入JSON", "error", 2000)
    return
  }
  
  try {
    const comp = JSON.parse(jsonStr)
    if (comp.type) {
      const presetComp = presetComponents.find(p => p.type === comp.type)
      elements.componentTypeSelect.value = presetComp ? presetComp.name : comp.type
    }
    if (comp.name) {
      elements.componentNameInput.value = comp.name
    }
    if (comp.params) {
      elements.componentParamsInput.value = JSON.stringify(comp.params, null, 2)
    }
    showNotification("导入成功，请检查并保存", "success", 2000)
  } catch (e) {
    showNotification("JSON格式错误：" + e.message, "error", 2000)
  }
}

// ============ 缺失的函数声明 ============

function closeComponentEdit() {
  elements.componentEditOverlay.classList.remove("active")
  editingStepIndex = null
  editingComponentIndex = null
  editingSection = null
}

function saveComponent() {
  const funcDesc = elements.componentNameInput.value.trim()
  if (!funcDesc) {
    showNotification("请输入组件功能描述", "error", 2000)
    return
  }

  const compNameValue = elements.componentTypeSelect.value.trim()
  if (!compNameValue) {
    showNotification("请选择组件名称", "error", 2000)
    return
  }

  let compType = "input"
  const presetComp = presetComponents.find(p => p.name === compNameValue)
  if (presetComp) {
    compType = presetComp.type
  } else if (selectedPresetComponent) {
    compType = selectedPresetComponent.type
  }

  let params
  try {
    params = JSON.parse(elements.componentParamsInput.value)
  } catch (e) {
    showNotification("参数格式错误，请输入有效的 JSON", "error", 2000)
    return
  }

  if (isEditingHistoryCase && isViewingTemplate && caseTemplate) {
    // 编辑模板时，保存到caseTemplate
    if (!caseTemplate[editingSection][editingStepIndex].components) {
      caseTemplate[editingSection][editingStepIndex].components = []
    }
    if (editingComponentIndex !== null) {
      caseTemplate[editingSection][editingStepIndex].components[editingComponentIndex] = {
        ...caseTemplate[editingSection][editingStepIndex].components[editingComponentIndex],
        type: compType,
        name: funcDesc,
        params,
      }
    } else {
      const newComp = {
        id: "c" + Date.now(),
        type: compType,
        name: funcDesc,
        params,
      }
      caseTemplate[editingSection][editingStepIndex].components.push(newComp)
    }
  } else if (isEditingHistoryCase) {
    // 编辑已选用例时，保存到historyCasesForEdit
    if (editingComponentIndex !== null) {
      historyCasesForEdit[currentEditCaseIndex][editingSection][editingStepIndex].components[editingComponentIndex] = {
        ...historyCasesForEdit[currentEditCaseIndex][editingSection][editingStepIndex].components[editingComponentIndex],
        type: compType,
        name: funcDesc,
        params,
      }
    } else {
      const newComp = {
        id: "c" + Date.now(),
        type: compType,
        name: funcDesc,
        params,
      }
      historyCasesForEdit[currentEditCaseIndex][editingSection][editingStepIndex].components.push(newComp)
    }
  } else {
    if (editingComponentIndex !== null) {
      testCases[currentCaseIndex][editingSection][editingStepIndex].components[editingComponentIndex] = {
        ...testCases[currentCaseIndex][editingSection][editingStepIndex].components[editingComponentIndex],
        type: compType,
        name: funcDesc,
        params,
      }
    } else {
      const newComp = {
        id: "c" + Date.now(),
        type: compType,
        name: funcDesc,
        params,
      }
      testCases[currentCaseIndex][editingSection][editingStepIndex].components.push(newComp)
    }
  }

  closeComponentEdit()
  if (isEditingHistoryCase) {
    renderHistoryEditDetail()
  } else {
    renderCaseDetail()
  }
}

function openComponentEdit(stepIndex, compIndex, section) {
  editingStepIndex = stepIndex
  editingComponentIndex = compIndex
  editingSection = section
  selectedPresetComponent = null
  isEditingHistoryCase = false  // 确保这是测试用例详情页面的编辑
  
  // 关键修复：重新绑定保存按钮为saveComponent
  elements.saveComponentBtn.onclick = saveComponent

  if (compIndex !== null) {
    const comp = testCases[currentCaseIndex][section][stepIndex].components[compIndex]
    elements.componentEditTitle.textContent = "编辑组件"
    const presetComp = presetComponents.find(p => p.type === comp.type)
    elements.componentTypeSelect.value = presetComp ? presetComp.name : comp.type
    elements.componentNameInput.value = comp.name
    elements.componentParamsInput.value = JSON.stringify(comp.params, null, 2)
    // 更新参数摘要显示
    updateParamSummary(comp.params)
  } else {
    elements.componentEditTitle.textContent = "添加组件"
    elements.componentTypeSelect.value = ""
    elements.componentNameInput.value = ""
    elements.componentParamsInput.value = "{}"
    // 清空参数摘要显示
    updateParamSummary({})
  }
  
  // 渲染预置组件下拉列表
  renderPresetComponentsDropdown()

  elements.componentEditOverlay.classList.add("active")
}

function initSearchableSelect(input, dropdown, options, renderFunc, selectFunc) {
  // Placeholder implementation
  console.log('initSearchableSelect called')
}

function renderStepOption(step) {
  return `<div>${step.name}</div>`
}

function onStepSelected(step) {
  selectedPresetStep = step
  elements.stepNameInput.value = step.name
  elements.stepDescInput.value = step.description || ""
}

function renderComponentOption(comp) {
  return `<div>${comp.name}</div>`
}

function onComponentSelected(comp) {
  selectedPresetComponent = comp
  elements.componentTypeSelect.value = comp.name
  if (comp.type && componentDefaultParams[comp.type]) {
    elements.componentParamsInput.value = JSON.stringify(componentDefaultParams[comp.type], null, 2)
  }
}

  // 启动应用
async function startApp() {
  init()
  
  // 从后端获取参数配置架构
  try {
    paramSchemas = await fetchParamSchemas()
    console.log('[v0] 参数配置架构已加载:', Object.keys(paramSchemas))
  } catch (error) {
    console.error('[v0] 获取参数配置架构失败:', error)
    showNotification('获取参数配置架构失败，请检查后端服务', 'error', 3000)
  }
}

startApp()

// 初始化presetSteps为默认值
presetSteps = defaultPresetSteps
presetComponents = defaultPresetComponents

// 在init后初始化历史搜索功能
initHistorySearchElements()
bindHistorySearchEvents()
initHistoryCaseEditElements()
bindHistoryCaseEditEvents()
