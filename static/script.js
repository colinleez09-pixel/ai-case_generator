// API 基础配置
const API_BASE_URL = '/api';
let currentSessionId = null;
let currentFileId = null;
let isGenerating = false;

// UI 状态管理
let instructionsExpanded = false; // 说明面板展开状态，默认折叠
let isFirstGeneration = true; // 跟踪是否是第一次生成

// 流式消息显示实例
let globalStreamingDisplay = null;

// 时间戳格式化函数
function formatTimestamp(date) {
  const now = new Date();
  const messageDate = new Date(date);
  
  // 检查是否是同一天
  const isSameDay = now.toDateString() === messageDate.toDateString();
  
  const hours = messageDate.getHours().toString().padStart(2, '0');
  const minutes = messageDate.getMinutes().toString().padStart(2, '0');
  const timeString = `${hours}:${minutes}`;
  
  if (isSameDay) {
    return timeString;
  } else {
    // 不同天显示月-日 时:分
    const month = (messageDate.getMonth() + 1).toString().padStart(2, '0');
    const day = messageDate.getDate().toString().padStart(2, '0');
    return `${month}-${day} ${timeString}`;
  }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
async function initializeApp() {
    try {
        // 加载配置数据
        await loadConfigData();
        
        // 初始化事件监听器
        init();
        
        // 初始化UI状态 - 禁用聊天功能
        initializeChatState();
        
        console.log('应用初始化完成');
    } catch (error) {
        console.error('应用初始化失败:', error);
        showMessage('应用初始化失败，请刷新页面重试', 'error');
    }
}

// 初始化聊天状态
function initializeChatState() {
    // 禁用聊天输入和发送按钮
    disableChatInput();
    
    // 清空聊天消息并显示初始消息
    if (elements.chatMessages) {
        elements.chatMessages.innerHTML = '';
        // 显示初始消息，提示用户先上传文件，使用流式效果
        addMessage("你好！我是 AI 测试用例生成助手。请先在左侧上传您的用例模板文件并点击\"开始生成\"，然后我们就可以开始对话来生成完整的测试用例了。", "ai", null, true);
    }
}

// 禁用聊天输入
function disableChatInput() {
    if (elements.chatInput) {
        elements.chatInput.disabled = true;
        elements.chatInput.placeholder = "请先上传文件并点击开始生成";
    }
    if (elements.sendBtn) {
        elements.sendBtn.disabled = true;
    }
    // 不显示禁用遮罩，让用户可以看到对话内容
    if (elements.chatDisabledOverlay) {
        elements.chatDisabledOverlay.classList.add("hidden");
    }
}

// 启用聊天输入
function enableChatInput() {
    if (elements.chatInput) {
        elements.chatInput.disabled = false;
        elements.chatInput.placeholder = "请输入您的问题...";
    }
    if (elements.sendBtn) {
        elements.sendBtn.disabled = false;
    }
    // 隐藏禁用遮罩
    if (elements.chatDisabledOverlay) {
        elements.chatDisabledOverlay.classList.add("hidden");
    }
}

// 加载配置数据
async function loadConfigData() {
    try {
        const response = await fetch(`${API_BASE_URL}/config/all`);
        const data = await response.json();
        
        if (data.success && data.config) {
            // 更新API版本选择器
            updateApiVersionSelect(data.config.api_versions);
            
            // 存储预设数据供后续使用
            window.presetSteps = data.config.preset_steps || presetSteps;
            window.presetComponents = data.config.preset_components || presetComponents;
            
            console.log('配置数据加载成功');
        } else {
            throw new Error(data.message || '加载配置数据失败');
        }
    } catch (error) {
        console.error('加载配置数据失败:', error);
        // 使用默认配置
        updateApiVersionSelect([
            { version: 'v1.0', name: 'API v1.0' },
            { version: 'v1.1', name: 'API v1.1' },
            { version: 'v2.0', name: 'API v2.0' },
            { version: 'v2.1', name: 'API v2.1' }
        ]);
        
        // 使用默认预设数据
        window.presetSteps = presetSteps;
        window.presetComponents = presetComponents;
    }
}

// 更新API版本选择器
function updateApiVersionSelect(apiVersions) {
    const select = document.getElementById('apiVersionSelect');
    if (!select) return;
    
    select.innerHTML = '<option value="">选择接口文档版本</option>';
    
    // 确保apiVersions是数组且不为空
    if (!Array.isArray(apiVersions) || apiVersions.length === 0) {
        console.warn('apiVersions不是数组或为空，使用默认配置');
        apiVersions = [
            { version: 'v1.0', name: 'API v1.0' },
            { version: 'v1.1', name: 'API v1.1' },
            { version: 'v2.0', name: 'API v2.0' },
            { version: 'v2.1', name: 'API v2.1' }
        ];
    }
    
    apiVersions.forEach(version => {
        if (version && version.version && version.name) {
            const option = document.createElement('option');
            option.value = version.version;
            option.textContent = version.name;
            select.appendChild(option);
        }
    });
}

// 重置生成按钮状态
function resetGenerateButtonState() {
    if (elements.generateBtn) {
        elements.generateBtn.disabled = false;
        elements.generateBtn.textContent = "开始生成";
    }
}

// 更新所有生成按钮为完成状态
function updateAllGenerateButtonsToCompleted() {
    isGenerating = false;
    
    // 左侧主生成按钮：恢复为可点击的"开始生成"状态，允许重新生成
    if (elements.generateBtn) {
        elements.generateBtn.disabled = false;
        elements.generateBtn.textContent = "开始生成";
    }
    
    // 聊天中的动态生成按钮：设置为"生成结束"并置灰
    const dynamicBtns = document.querySelectorAll('#startGenerateBtn, [id^="startGenerateBtn_"]');
    dynamicBtns.forEach(btn => {
        btn.disabled = true;
        btn.textContent = "生成结束";
    });
}

// 重置所有状态，准备新的生成流程
function resetAllStatesForNewGeneration() {
    // 重置生成状态
    isGenerating = false;
    generationComplete = false;
    canDownload = false;
    
    // 重置会话相关变量
    currentSessionId = null;
    currentFileId = null;
    testCases = [];
    
    // 重置按钮状态
    resetGenerateButtonState();
    
    // 清理可能存在的旧按钮
    const oldDynamicBtns = document.querySelectorAll('#startGenerateBtn');
    oldDynamicBtns.forEach(btn => {
        btn.remove();
    });
    
    console.log('🔄 所有状态已重置，准备新的生成流程');
}

// 显示消息
function showMessage(message, type = 'info') {
    // 简单的消息显示，可以后续改进
    if (type === 'error') {
        console.error(message);
        alert('错误: ' + message);
    } else {
        console.log(message);
    }
}
const mockTestCases = [
  {
    id: "TC001",
    name: "用户登录功能测试",
    preconditions: [
      {
        id: "pre1",
        name: "用户已注册账号",
        expanded: false,
        components: [
          {
            id: "prec1",
            type: "api",
            name: "接口调用 - 检查用户存在",
            params: { method: "GET", url: "/api/users/check", expected: true },
          },
        ],
      },
      {
        id: "pre2",
        name: "系统登录功能正常可用",
        expanded: false,
        components: [
          {
            id: "prec2",
            type: "assert",
            name: "断言 - 登录页面可访问",
            params: { type: "status", expected: 200 },
          },
        ],
      },
    ],
    steps: [
      {
        id: "s1",
        name: "打开登录页面",
        expanded: true,
        components: [
          {
            id: "c1",
            type: "input",
            name: "输入框 - 用户名",
            params: { value: "testuser@example.com", validation: "email" },
          },
          {
            id: "c2",
            type: "input",
            name: "输入框 - 密码",
            params: { value: "Password123!", encrypted: true },
          },
        ],
      },
      {
        id: "s2",
        name: "输入用户名和密码",
        expanded: false,
        components: [
          {
            id: "c3",
            type: "button",
            name: "按钮 - 登录",
            params: { id: "login-btn", text: "登录" },
          },
        ],
      },
      {
        id: "s3",
        name: "点击登录按钮",
        expanded: false,
        components: [
          {
            id: "c4",
            type: "assert",
            name: "断言 - 跳转验证",
            params: { type: "url", expected: "/dashboard", timeout: 5000 },
          },
        ],
      },
    ],
    expectedResults: [
      {
        id: "exp1",
        name: "成功跳转到用户仪表板页面",
        expanded: false,
        components: [
          {
            id: "expc1",
            type: "assert",
            name: "断言 - URL验证",
            params: { type: "url", expected: "/dashboard" },
          },
        ],
      },
      {
        id: "exp2",
        name: "页面显示用户欢迎信息",
        expanded: false,
        components: [
          {
            id: "expc2",
            type: "assert",
            name: "断言 - 文本验证",
            params: { type: "text", selector: ".welcome", contains: "欢迎" },
          },
        ],
      },
    ],
  },
  {
    id: "TC002",
    name: "商品搜索功能测试",
    preconditions: [
      {
        id: "pre3",
        name: "商品数据库中有测试商品数据",
        expanded: false,
        components: [
          {
            id: "prec3",
            type: "api",
            name: "接口调用 - 检查商品数据",
            params: { method: "GET", url: "/api/products/count", minCount: 1 },
          },
        ],
      },
    ],
    steps: [
      {
        id: "s4",
        name: "进入商品列表页",
        expanded: false,
        components: [
          {
            id: "c5",
            type: "api",
            name: "接口调用 - 获取商品列表",
            params: { method: "GET", url: "/api/products", headers: { "Content-Type": "application/json" } },
          },
        ],
      },
      {
        id: "s5",
        name: "输入搜索关键词",
        expanded: false,
        components: [
          {
            id: "c6",
            type: "input",
            name: "输入框 - 搜索",
            params: { value: "iPhone 15", placeholder: "请输入商品名称" },
          },
        ],
      },
    ],
    expectedResults: [
      {
        id: "exp3",
        name: "搜索结果列表正确显示匹配商品",
        expanded: false,
        components: [
          {
            id: "expc3",
            type: "assert",
            name: "断言 - 结果数量",
            params: { type: "count", selector: ".product-item", min: 1 },
          },
        ],
      },
    ],
  },
  {
    id: "TC003",
    name: "购物车添加商品测试",
    preconditions: [
      {
        id: "pre4",
        name: "用户已登录",
        expanded: false,
        components: [
          {
            id: "prec4",
            type: "assert",
            name: "断言 - 登录状态",
            params: { type: "cookie", name: "auth_token", exists: true },
          },
        ],
      },
      {
        id: "pre5",
        name: "商品库存充足",
        expanded: false,
        components: [
          {
            id: "prec5",
            type: "api",
            name: "接口调用 - 检查库存",
            params: { method: "GET", url: "/api/products/stock", minStock: 1 },
          },
        ],
      },
    ],
    steps: [
      {
        id: "s6",
        name: "选择商品规格",
        expanded: false,
        components: [
          {
            id: "c7",
            type: "select",
            name: "下拉选择 - 颜色",
            params: { options: ["黑色", "白色", "蓝色"], selected: "黑色" },
          },
          {
            id: "c8",
            type: "select",
            name: "下拉选择 - 容量",
            params: { options: ["128GB", "256GB", "512GB"], selected: "256GB" },
          },
        ],
      },
      {
        id: "s7",
        name: "点击加入购物车",
        expanded: false,
        components: [
          {
            id: "c9",
            type: "button",
            name: "按钮 - 加入购物车",
            params: { id: "add-to-cart", text: "加入购物车" },
          },
        ],
      },
    ],
    expectedResults: [
      {
        id: "exp4",
        name: "购物车数量增加1",
        expanded: false,
        components: [
          {
            id: "expc4",
            type: "assert",
            name: "断言 - 购物车数量",
            params: { type: "text", selector: ".cart-count", expected: "1" },
          },
        ],
      },
      {
        id: "exp5",
        name: "显示添加成功提示",
        expanded: false,
        components: [
          {
            id: "expc5",
            type: "assert",
            name: "断言 - 提示信息",
            params: { type: "visible", selector: ".success-toast" },
          },
        ],
      },
    ],
  },
]

// 组件默认参数配置（模拟从后台获取）
const componentDefaultParams = {
  input: {
    value: "",
    placeholder: "请输入内容",
    validation: "text",
    maxLength: 100,
  },
  button: {
    id: "btn-id",
    text: "按钮文本",
    type: "submit",
  },
  select: {
    options: ["选项1", "选项2", "选项3"],
    selected: "",
    placeholder: "请选择",
  },
  checkbox: {
    checked: false,
    label: "复选框标签",
  },
  api: {
    method: "GET",
    url: "/api/endpoint",
    headers: { "Content-Type": "application/json" },
    body: {},
  },
  assert: {
    type: "equals",
    expected: "",
    timeout: 5000,
  },
}

const presetSteps = [
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

const presetComponents = [
  { id: "comp_input", type: "input", name: "输入框", icon: "edit", description: "文本输入组件" },
  { id: "comp_button", type: "button", name: "按钮", icon: "pointer", description: "点击操作组件" },
  { id: "comp_select", type: "select", name: "下拉选择", icon: "list", description: "下拉选择组件" },
  { id: "comp_checkbox", type: "checkbox", name: "复选框", icon: "check-square", description: "复选框组件" },
  { id: "comp_api", type: "api", name: "接口调用", icon: "globe", description: "HTTP接口请求组件" },
  { id: "comp_assert", type: "assert", name: "断言验证", icon: "check-circle", description: "验证断言组件" },
  { id: "comp_wait", type: "wait", name: "等待", icon: "clock", description: "延时等待组件" },
  { id: "comp_scroll", type: "scroll", name: "滚动", icon: "arrow-down", description: "页面滚动组件" },
  { id: "comp_upload", type: "upload", name: "文件上传", icon: "upload", description: "文件上传组件" },
  { id: "comp_screenshot", type: "screenshot", name: "截图", icon: "camera", description: "页面截图组件" },
]

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

let generationComplete = false
let canDownload = false

let testCasesBackup = null

let progressCounter = 0

// 新增用于存储选中的预设步骤
let selectedPresetStep = null
// 新增用于存储选中的预设组件
let selectedPresetComponent = null

// DOM 元素
const elements = {}

// 初始化DOM元素引用
function initElements() {
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
  elements.chatDisabledOverlay = document.getElementById("chatDisabledOverlay")
  elements.chatActionButtons = document.getElementById("chatActionButtons")
  elements.chatInputArea = document.getElementById("chatInputArea")
  elements.generateBtn = document.getElementById("generateBtn")
  elements.modalOverlay = document.getElementById("modalOverlay")
  elements.closeModalBtn = document.getElementById("closeModalBtn")
  elements.continueGenerateBtn = document.getElementById("continueGenerateBtn")
  elements.downloadBtn = document.getElementById("downloadBtn")
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

  elements.stepNameSelectWrapper = document.getElementById("stepNameSelectWrapper")
  elements.stepNameDropdown = document.getElementById("stepNameDropdown")
  elements.componentNameSelectWrapper = document.getElementById("componentNameSelectWrapper")
  elements.componentNameDropdown = document.getElementById("componentNameDropdown")

  // 说明面板元素
  elements.instructionsCard = document.getElementById("instructionsCard")
  elements.instructionsHeader = document.getElementById("instructionsHeader")
  elements.instructionsContent = document.getElementById("instructionsContent")
  elements.instructionsExpandIcon = document.getElementById("instructionsExpandIcon")
}

// 初始化
function init() {
  initElements()

  // 复选框事件
  elements.historyCheckbox.addEventListener("change", () => {
    elements.historyUploadZone.style.display = elements.historyCheckbox.checked ? "block" : "none"
  })

  elements.awCheckbox.addEventListener("change", () => {
    elements.awUploadZone.style.display = elements.awCheckbox.checked ? "block" : "none"
  })

  // 上传区域
  setupUploadZone(
    elements.historyUploadZone,
    elements.historyFileInput,
    elements.historyFileDisplay,
    elements.historyFileName,
  )
  setupUploadZone(elements.caseUploadZone, elements.caseFileInput, elements.caseFileDisplay, elements.caseFileName)
  setupUploadZone(elements.awUploadZone, elements.awFileInput, elements.awFileDisplay, elements.awFileName)

  // 移除文件
  elements.removeHistoryFile.addEventListener("click", () => removeFile("history"))
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
  elements.downloadBtn.addEventListener("click", downloadFile)

  // 添加按钮事件
  elements.addPreconditionBtn.addEventListener("click", () => openStepEdit(null, "preconditions"))
  elements.addStepBtn.addEventListener("click", () => openStepEdit(null, "steps"))
  elements.addExpectedResultBtn.addEventListener("click", () => openStepEdit(null, "expectedResults"))

  // 步骤编辑弹窗
  elements.closeStepEditBtn.addEventListener("click", closeStepEdit)
  elements.cancelStepEditBtn.addEventListener("click", closeStepEdit)
  elements.saveStepBtn.addEventListener("click", saveStep)

  // 组件编辑弹窗
  elements.closeComponentEditBtn.addEventListener("click", closeComponentEdit)
  elements.cancelComponentEditBtn.addEventListener("click", closeComponentEdit)
  elements.saveComponentBtn.addEventListener("click", saveComponent)
  // elements.componentTypeSelect.addEventListener("change", loadComponentDefaultParams)

  initSearchableSelect(elements.stepNameInput, elements.stepNameDropdown, presetSteps, renderStepOption, onStepSelected)

  initSearchableSelect(
    elements.componentTypeSelect,
    elements.componentNameDropdown,
    presetComponents,
    renderComponentOption,
    onComponentSelected,
  )

  // 确认弹窗
  elements.closeConfirmBtn.addEventListener("click", closeConfirm)
  elements.confirmCancelBtn.addEventListener("click", closeConfirm)
  elements.confirmOkBtn.addEventListener("click", confirmContinueGenerate)

  // 说明面板折叠功能
  elements.instructionsHeader.addEventListener("click", toggleInstructions)
  elements.instructionsHeader.addEventListener("keydown", handleInstructionsKeydown)
  
  // 初始化说明面板状态（默认折叠）
  initializeInstructionsState()
}

// 设置上传区域
function setupUploadZone(zone, input, display, fileName) {
  // 清除现有事件监听器
  zone.replaceWith(zone.cloneNode(true));
  input.replaceWith(input.cloneNode(true));
  
  // 重新获取元素引用
  zone = document.getElementById(zone.id);
  input = document.getElementById(input.id);
  
  // 更新全局元素引用
  if (zone.id === 'historyUploadZone') {
    elements.historyUploadZone = zone;
    elements.historyFileInput = input;
  } else if (zone.id === 'caseUploadZone') {
    elements.caseUploadZone = zone;
    elements.caseFileInput = input;
  } else if (zone.id === 'awUploadZone') {
    elements.awUploadZone = zone;
    elements.awFileInput = input;
  }
  
  // 添加事件监听器
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

// 开始生成
async function startGeneration() {
  const caseFileUploaded = elements.caseFileDisplay.style.display === "flex"
  const apiVersionSelected = document.getElementById("apiVersionSelect").value !== ""

  if (!caseFileUploaded) {
    showFriendlyError("请先上传需要生成的用例文件", {
      showSuggestions: true,
      suggestions: [
        "点击上传区域选择XML格式的用例文件",
        "确保文件格式正确且完整",
        "如需帮助，请查看使用说明"
      ]
    });
    return
  }

  if (!apiVersionSelected) {
    showFriendlyError("请选择接口文档版本", {
      showSuggestions: true,
      suggestions: [
        "在下拉菜单中选择对应的API版本",
        "如不确定版本，请咨询相关人员",
        "选择最新版本通常是安全的选择"
      ]
    });
    return
  }

  // 重置所有状态，准备新的生成流程
  resetAllStatesForNewGeneration();

  hideActionButtons()

  // 创建进度指示器实例
  const progressIndicator = new ProgressIndicator();
  
  // 显示上传阶段
  progressIndicator.showStage('UPLOADING');

  // 禁用生成按钮并显示生成中状态
  elements.generateBtn.disabled = true
  elements.generateBtn.textContent = "生成中..."

  // 启用聊天功能
  enableChatInput()
  isGenerating = true

  // 准备文件数据（移到函数顶部，避免作用域问题）
  const formData = new FormData();
  
  // 添加必需的用例模板文件
  const caseFile = elements.caseFileInput.files[0];
  if (caseFile) {
    formData.append('case_template', caseFile);
  }
  
  // 添加可选的历史用例文件
  if (elements.historyCheckbox.checked && elements.historyFileInput.files[0]) {
    formData.append('history_case', elements.historyFileInput.files[0]);
  }
  
  // 添加可选的AW模板文件
  if (elements.awCheckbox.checked && elements.awFileInput.files[0]) {
    formData.append('aw_template', elements.awFileInput.files[0]);
  }
  
  // 添加配置信息
  const config = {
    api_version: document.getElementById("apiVersionSelect").value
  };
  formData.append('config', JSON.stringify(config));

  try {
    // 根据是否是第一次生成来决定是否清空聊天记录
    if (isFirstGeneration) {
      // 第一次生成：清空聊天记录
      elements.chatMessages.innerHTML = '';
    } else {
      // 后续生成：保留对话历史，添加会话分隔符
      addSessionSeparator();
    }
    
    // 更新进度到解析阶段
    progressIndicator.showStage('PARSING');
    
    // 模拟文件处理进度
    await simulateProgress(progressIndicator, 'PARSING', 1000);
    
    // 更新进度到连接阶段
    progressIndicator.showStage('CONNECTING');
    
    // 调用后台API开始生成任务
    const response = await fetch(`${API_BASE_URL}/generation/start`, {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      currentSessionId = result.session_id;
      
      // 更新进度到分析阶段
      progressIndicator.showStage('ANALYZING');
      
      // 显示响应时间信息（如果有）
      if (result.response_time) {
        const responseTime = result.response_time.toFixed(2);
        console.log(`文件处理完成，响应时间: ${responseTime}s`);
        
        if (result.response_time > 3.0) {
          addMessage(`文件处理完成（耗时 ${responseTime}s，稍长于预期，我们正在优化性能）`, "ai");
        }
      }
      
      // 如果有自动分析，显示思考阶段
      if (result.auto_chat_started) {
        progressIndicator.showStage('THINKING');
        
        // 模拟AI思考过程
        await simulateProgress(progressIndicator, 'THINKING', 1500);
      }
      
      // 隐藏进度指示器
      progressIndicator.hide();
      
      // 处理自动分析结果
      await handleUploadComplete(result);
      
      // 标记不再是第一次生成
      isFirstGeneration = false;
      
    } else {
      throw new Error(result.message || '启动生成任务失败');
    }
    
  } catch (error) {
    console.error('启动生成失败:', error);
    
    // 显示错误状态
    progressIndicator.showError(
      `启动失败: ${error.message}`,
      () => startGeneration()
    );
    
    // 恢复UI状态
    resetGenerateButtonState();
    disableChatInput();
    isGenerating = false;
  }
}

/**
 * 模拟进度更新
 * @param {ProgressIndicator} progressIndicator - 进度指示器实例
 * @param {string} stage - 当前阶段
 * @param {number} duration - 持续时间(ms)
 */
async function simulateProgress(progressIndicator, stage, duration) {
  const steps = 20;
  const stepDuration = duration / steps;
  
  for (let i = 0; i <= steps; i++) {
    const progress = (i / steps) * 100;
    progressIndicator.updateProgress(progress);
    
    if (i < steps) {
      await new Promise(resolve => setTimeout(resolve, stepDuration));
    }
  }
}

/**
 * 处理文件上传完成后的自动分析
 * @param {Object} response - 后端返回的响应数据
 */
async function handleUploadComplete(response) {
  try {
    // 1. 检查是否启动了自动分析
    if (response.auto_chat_started) {
      console.log('🤖 检测到自动分析已启动');
      
      // 显示用户发送的消息（包含文件名和用例描述）
      const uploadedFileName = getUploadedFileName();
      if (uploadedFileName && response.initial_analysis) {
        let userMessage = `我上传了一个测试用例文件：${uploadedFileName}\n\n`;
        
        // 如果有提取的用例描述，显示出来
        if (response.initial_analysis.description) {
          userMessage += `以下是文件中的测试用例内容：\n\n${response.initial_analysis.description}\n\n`;
        }
        
        userMessage += `请帮我分析这个测试用例，并提出完善建议。我希望能够生成更完整和规范的测试用例。`;
        
        addMessage(userMessage, "user");
      } else if (uploadedFileName) {
        // 如果没有用例描述，只显示文件名
        addMessage(`我上传了用例文件：${uploadedFileName}`, "user");
      }
      
      // 显示AI的回复（Dify的响应），使用流式效果
      if (response.message) {
        addMessage(response.message, "ai", null, true);
      }
      
    } else {
      // 没有自动分析，显示文件名作为用户消息
      const uploadedFileName = getUploadedFileName();
      if (uploadedFileName) {
        addMessage(`我上传了用例文件：${uploadedFileName}`, "user");
      }
      
      // 显示默认的AI回复，使用流式效果
      if (response.analysis_result) {
        addMessage(response.analysis_result, "ai", null, true);
      } else {
        addMessage(
          "我已经收到了您的用例文件。为了生成更准确的测试用例，请问：\n\n1. 这个系统主要的用户群体是谁？\n2. 是否有特殊的安全性要求？",
          "ai",
          null,
          true
        );
      }
    }
    
  } catch (error) {
    console.error('处理上传完成事件失败:', error);
    
    // 降级处理：显示基本的成功消息
    const uploadedFileName = getUploadedFileName();
    if (uploadedFileName) {
      addMessage(`我上传了用例文件：${uploadedFileName}`, "user");
    }
    addMessage("文件上传成功，请开始与AI对话来生成测试用例。", "ai", null, true);
  }
}

/**
 * 获取上传的文件名
 * @returns {string} 文件名
 */
function getUploadedFileName() {
  // 获取用例模板文件名
  if (elements.caseFileDisplay && elements.caseFileDisplay.style.display === "flex") {
    return elements.caseFileName ? elements.caseFileName.textContent : "用例文件";
  }
  return null;
}

/**
 * 显示加载状态指示器
 * @param {string} message - 加载消息
 * @param {string} containerId - 容器ID
 * @returns {string} 加载指示器ID
 */
function showLoadingIndicator(message = "处理中...", containerId = "chatMessages") {
  const loadingId = `loading_${Date.now()}`;
  const container = document.getElementById(containerId);
  
  if (!container) {
    console.error(`容器不存在: ${containerId}`);
    return null;
  }
  
  const loadingHtml = `
    <div class="loading-indicator" id="${loadingId}">
      <div class="loading-spinner">
        <div class="spinner"></div>
      </div>
      <div class="loading-message">${message}</div>
      <div class="loading-dots">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>
  `;
  
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message ai-message";
  loadingDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">${loadingHtml}</div>
  `;
  
  container.appendChild(loadingDiv);
  container.scrollTop = container.scrollHeight;
  
  return loadingId;
}

/**
 * 隐藏加载状态指示器
 * @param {string} loadingId - 加载指示器ID
 */
function hideLoadingIndicator(loadingId) {
  if (loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
      const messageElement = loadingElement.closest('.message');
      if (messageElement) {
        messageElement.remove();
      }
    }
  }
}

/**
 * 更新加载状态指示器的消息
 * @param {string} loadingId - 加载指示器ID
 * @param {string} message - 新的加载消息
 */
function updateLoadingMessage(loadingId, message) {
  if (loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
      const messageElement = loadingElement.querySelector('.loading-message');
      if (messageElement) {
        messageElement.textContent = message;
      }
    }
  }
}

/**
 * 流式消息显示类 - 提供打字机效果的消息显示
 */
class StreamingMessageDisplay {
  constructor(containerId = "chatMessages", options = {}) {
    this.containerId = containerId;
    this.currentMessageId = null;
    this.isStreaming = false;
    this.isPaused = false;
    this.streamingQueue = [];
    this.currentText = '';
    this.displayedText = '';
    this.typingTimer = null;
    this.cursorTimer = null;
    
    // 配置选项
    this.options = {
      typingSpeed: 40,        // 每秒字符数
      cursorBlinkRate: 500,   // 光标闪烁间隔(ms)
      autoScroll: true,       // 自动滚动到最新消息
      showCursor: true,       // 显示打字光标
      allowSkip: true,        // 允许跳过动画
      ...options
    };
    
    // 流式状态
    this.STATES = {
      IDLE: 'idle',
      STARTING: 'starting',
      STREAMING: 'streaming',
      PAUSED: 'paused',
      COMPLETED: 'completed',
      ERROR: 'error'
    };
    
    this.currentState = this.STATES.IDLE;
  }

  /**
   * 开始流式显示消息
   * @param {string} messageId - 消息ID（可选，自动生成）
   * @param {string} initialText - 初始文本（可选）
   */
  startStreaming(messageId = null, initialText = '') {
    if (this.isStreaming) {
      console.warn('已有流式消息在进行中');
      return null;
    }

    this.currentMessageId = messageId || `streaming_${Date.now()}`;
    this.currentText = initialText;
    this.displayedText = '';
    this.isStreaming = true;
    this.isPaused = false;
    this.currentState = this.STATES.STARTING;
    
    // 创建消息容器
    this._createMessageContainer();
    
    // 开始光标闪烁
    if (this.options.showCursor) {
      this._startCursorBlink();
    }
    
    this.currentState = this.STATES.STREAMING;
    console.log(`🎬 开始流式显示: ${this.currentMessageId}`);
    
    return this.currentMessageId;
  }

  /**
   * 追加文本到流式消息
   * @param {string} text - 要追加的文本
   */
  appendText(text) {
    if (!this.isStreaming || !this.currentMessageId) {
      console.warn('没有活跃的流式消息');
      return;
    }

    if (this.isPaused) {
      // 如果暂停中，将文本加入队列
      this.streamingQueue.push(text);
      return;
    }

    this.currentText += text;
    this._processTypingEffect();
  }

  /**
   * 完成流式显示
   */
  finishStreaming() {
    if (!this.isStreaming) {
      return;
    }

    // 清除定时器
    this._clearTimers();
    
    // 显示完整文本
    this.displayedText = this.currentText;
    this._updateMessageContent();
    
    // 移除光标
    this._removeCursor();
    
    // 重置状态
    this.isStreaming = false;
    this.isPaused = false;
    this.currentState = this.STATES.COMPLETED;
    
    console.log(`✅ 流式显示完成: ${this.currentMessageId}`);
    
    // 自动滚动
    if (this.options.autoScroll) {
      this._scrollToBottom();
    }
  }

  /**
   * 暂停流式显示
   */
  pauseStreaming() {
    if (!this.isStreaming || this.isPaused) {
      return;
    }

    this.isPaused = true;
    this.currentState = this.STATES.PAUSED;
    this._clearTimers();
    
    console.log(`⏸️ 暂停流式显示: ${this.currentMessageId}`);
  }

  /**
   * 恢复流式显示
   */
  resumeStreaming() {
    if (!this.isStreaming || !this.isPaused) {
      return;
    }

    this.isPaused = false;
    this.currentState = this.STATES.STREAMING;
    
    // 处理队列中的文本
    while (this.streamingQueue.length > 0) {
      const queuedText = this.streamingQueue.shift();
      this.currentText += queuedText;
    }
    
    // 恢复打字效果
    this._processTypingEffect();
    
    // 恢复光标闪烁
    if (this.options.showCursor) {
      this._startCursorBlink();
    }
    
    console.log(`▶️ 恢复流式显示: ${this.currentMessageId}`);
  }

  /**
   * 跳过动画，直接显示完整内容
   */
  skipAnimation() {
    if (!this.isStreaming || !this.options.allowSkip) {
      return;
    }

    console.log(`⏭️ 跳过动画: ${this.currentMessageId}`);
    this.finishStreaming();
  }

  /**
   * 获取当前状态
   */
  getState() {
    return {
      state: this.currentState,
      isStreaming: this.isStreaming,
      isPaused: this.isPaused,
      messageId: this.currentMessageId,
      progress: this.currentText.length > 0 ? this.displayedText.length / this.currentText.length : 0
    };
  }

  /**
   * 创建消息容器
   * @private
   */
  _createMessageContainer() {
    const container = document.getElementById(this.containerId);
    if (!container) {
      console.error(`容器不存在: ${this.containerId}`);
      return;
    }

    // 创建流式消息的HTML结构
    const streamingHtml = `
      <div class="streaming-message-display" id="${this.currentMessageId}">
        <div class="streaming-content">
          <span class="streaming-text"></span>
          ${this.options.showCursor ? '<span class="typing-cursor">|</span>' : ''}
        </div>
        ${this.options.allowSkip ? `
          <div class="streaming-controls">
            <button class="streaming-control-btn pause-btn" title="暂停">⏸️</button>
            <button class="streaming-control-btn skip-btn" title="跳过动画">⏭️</button>
          </div>
        ` : ''}
      </div>
    `;

    // 创建完整的消息容器
    const messageDiv = document.createElement("div");
    messageDiv.className = "message ai-message streaming-message-container";
    messageDiv.innerHTML = `
      <div class="message-avatar">Agent</div>
      <div class="message-content">
        ${streamingHtml}
      </div>
    `;

    container.appendChild(messageDiv);
    
    // 绑定控制按钮事件
    if (this.options.allowSkip) {
      this._bindControlEvents(messageDiv);
    }
    
    // 自动滚动
    if (this.options.autoScroll) {
      this._scrollToBottom();
    }
  }

  /**
   * 绑定控制按钮事件
   * @private
   */
  _bindControlEvents(messageDiv) {
    const pauseBtn = messageDiv.querySelector('.pause-btn');
    const skipBtn = messageDiv.querySelector('.skip-btn');
    
    if (pauseBtn) {
      pauseBtn.addEventListener('click', () => {
        if (this.isPaused) {
          this.resumeStreaming();
          pauseBtn.textContent = '⏸️';
          pauseBtn.title = '暂停';
        } else {
          this.pauseStreaming();
          pauseBtn.textContent = '▶️';
          pauseBtn.title = '继续';
        }
      });
    }
    
    if (skipBtn) {
      skipBtn.addEventListener('click', () => {
        this.skipAnimation();
      });
    }
  }

  /**
   * 处理打字效果
   * @private
   */
  _processTypingEffect() {
    if (this.isPaused || !this.isStreaming) {
      return;
    }

    const remainingText = this.currentText.slice(this.displayedText.length);
    if (remainingText.length === 0) {
      return;
    }

    // 计算打字间隔
    const typingInterval = 1000 / this.options.typingSpeed;
    
    // 逐字显示
    this.typingTimer = setTimeout(() => {
      if (this.isPaused || !this.isStreaming) {
        return;
      }

      // 添加下一个字符
      this.displayedText = this.currentText.slice(0, this.displayedText.length + 1);
      this._updateMessageContent();
      
      // 自动滚动
      if (this.options.autoScroll) {
        this._scrollToBottom();
      }
      
      // 继续处理剩余文本
      if (this.displayedText.length < this.currentText.length) {
        this._processTypingEffect();
      }
    }, typingInterval);
  }

  /**
   * 更新消息内容
   * @private
   */
  _updateMessageContent() {
    const messageElement = document.getElementById(this.currentMessageId);
    if (!messageElement) {
      return;
    }

    const textElement = messageElement.querySelector('.streaming-text');
    if (textElement) {
      // 处理换行和HTML转义
      const formattedText = this.displayedText.replace(/\n/g, '<br>');
      textElement.innerHTML = formattedText;
    }
  }

  /**
   * 开始光标闪烁
   * @private
   */
  _startCursorBlink() {
    const messageElement = document.getElementById(this.currentMessageId);
    if (!messageElement) {
      return;
    }

    const cursor = messageElement.querySelector('.typing-cursor');
    if (!cursor) {
      return;
    }

    this.cursorTimer = setInterval(() => {
      if (cursor) {
        cursor.style.opacity = cursor.style.opacity === '0' ? '1' : '0';
      }
    }, this.options.cursorBlinkRate);
  }

  /**
   * 移除光标
   * @private
   */
  _removeCursor() {
    const messageElement = document.getElementById(this.currentMessageId);
    if (!messageElement) {
      return;
    }

    const cursor = messageElement.querySelector('.typing-cursor');
    if (cursor) {
      cursor.remove();
    }
  }

  /**
   * 清除定时器
   * @private
   */
  _clearTimers() {
    if (this.typingTimer) {
      clearTimeout(this.typingTimer);
      this.typingTimer = null;
    }
    
    if (this.cursorTimer) {
      clearInterval(this.cursorTimer);
      this.cursorTimer = null;
    }
  }

  /**
   * 滚动到底部
   * @private
   */
  _scrollToBottom() {
    const container = document.getElementById(this.containerId);
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }
}

/**
 * 进度指示器类 - 提供增强的进度显示功能
 */
class ProgressIndicator {
  constructor(containerId = "chatMessages") {
    this.containerId = containerId;
    this.currentIndicatorId = null;
    this.currentStage = null;
    this.isVisible = false;
    
    // 进度阶段定义
    this.STAGES = {
      UPLOADING: { 
        name: '上传文件', 
        icon: '📤', 
        message: '正在上传文件...',
        color: '#3b82f6'
      },
      PARSING: { 
        name: '解析文件', 
        icon: '📋', 
        message: '正在解析用例文件...',
        color: '#8b5cf6'
      },
      CONNECTING: { 
        name: '连接AI', 
        icon: '🔗', 
        message: '正在连接AI服务...',
        color: '#06b6d4'
      },
      ANALYZING: { 
        name: '分析内容', 
        icon: '🤖', 
        message: '正在分析用例内容...',
        color: '#10b981'
      },
      THINKING: { 
        name: 'AI思考', 
        icon: '💭', 
        message: 'AI正在思考中，请稍候...',
        color: '#f59e0b'
      },
      STREAMING: {
        name: '接收回复',
        icon: '💬',
        message: 'AI正在回复中...',
        color: '#ef4444'
      }
    };
  }

  /**
   * 显示特定阶段的进度
   * @param {string} stageName - 阶段名称 (UPLOADING, PARSING, etc.)
   * @param {string} customMessage - 自定义消息（可选）
   * @param {number} progress - 进度百分比（可选，0-100）
   */
  showStage(stageName, customMessage = null, progress = null) {
    const stage = this.STAGES[stageName];
    if (!stage) {
      console.error(`未知的进度阶段: ${stageName}`);
      return;
    }

    const message = customMessage || stage.message;
    this.currentStage = stageName;

    if (this.isVisible && this.currentIndicatorId) {
      // 更新现有指示器
      this._updateIndicator(stage, message, progress);
    } else {
      // 创建新的指示器
      this._createIndicator(stage, message, progress);
    }
  }

  /**
   * 更新当前阶段的进度
   * @param {number} percentage - 进度百分比 (0-100)
   */
  updateProgress(percentage) {
    if (!this.isVisible || !this.currentIndicatorId) {
      return;
    }

    const progressBar = document.querySelector(`#${this.currentIndicatorId} .progress-bar-fill`);
    const progressText = document.querySelector(`#${this.currentIndicatorId} .progress-percentage`);
    
    if (progressBar) {
      progressBar.style.width = `${percentage}%`;
    }
    if (progressText) {
      progressText.textContent = `${Math.round(percentage)}%`;
    }
  }

  /**
   * 显示错误状态
   * @param {string} message - 错误消息
   * @param {Function} retryCallback - 重试回调函数（可选）
   */
  showError(message, retryCallback = null) {
    const container = document.getElementById(this.containerId);
    if (!container) {
      console.error(`容器不存在: ${this.containerId}`);
      return;
    }

    // 隐藏当前指示器
    this.hide();

    const errorId = `error_${Date.now()}`;
    const retryButton = retryCallback ? `
      <button class="retry-button" onclick="this.retryCallback()">
        <span class="retry-icon">🔄</span>
        重试
      </button>
    ` : '';

    const errorHtml = `
      <div class="error-indicator" id="${errorId}">
        <div class="error-icon">⚠️</div>
        <div class="error-message">${message}</div>
        ${retryButton}
      </div>
    `;

    const errorDiv = document.createElement("div");
    errorDiv.className = "message ai-message error-message-container";
    errorDiv.innerHTML = `
      <div class="message-avatar">Agent</div>
      <div class="message-content">${errorHtml}</div>
    `;

    // 绑定重试回调
    if (retryCallback) {
      const retryBtn = errorDiv.querySelector('.retry-button');
      if (retryBtn) {
        retryBtn.retryCallback = retryCallback;
      }
    }

    container.appendChild(errorDiv);
    container.scrollTop = container.scrollHeight;
  }

  /**
   * 隐藏进度指示器
   */
  hide() {
    if (this.currentIndicatorId) {
      const indicatorElement = document.getElementById(this.currentIndicatorId);
      if (indicatorElement) {
        const messageElement = indicatorElement.closest('.message');
        if (messageElement) {
          messageElement.remove();
        }
      }
    }
    
    this.currentIndicatorId = null;
    this.currentStage = null;
    this.isVisible = false;
  }

  /**
   * 创建新的进度指示器
   * @private
   */
  _createIndicator(stage, message, progress) {
    const container = document.getElementById(this.containerId);
    if (!container) {
      console.error(`容器不存在: ${this.containerId}`);
      return;
    }

    this.currentIndicatorId = `progress_${Date.now()}`;
    
    const progressBarHtml = progress !== null ? `
      <div class="progress-bar-container">
        <div class="progress-bar">
          <div class="progress-bar-fill" style="width: ${progress}%; background-color: ${stage.color}"></div>
        </div>
        <div class="progress-percentage">${Math.round(progress)}%</div>
      </div>
    ` : '';

    const indicatorHtml = `
      <div class="enhanced-progress-indicator" id="${this.currentIndicatorId}">
        <div class="progress-header">
          <div class="progress-icon" style="color: ${stage.color}">${stage.icon}</div>
          <div class="progress-stage-name">${stage.name}</div>
        </div>
        <div class="progress-message">${message}</div>
        ${progressBarHtml}
        <div class="progress-spinner">
          <div class="spinner-ring" style="border-top-color: ${stage.color}"></div>
        </div>
      </div>
    `;

    const messageDiv = document.createElement("div");
    messageDiv.className = "message ai-message progress-message-container";
    messageDiv.innerHTML = `
      <div class="message-avatar">Agent</div>
      <div class="message-content">${indicatorHtml}</div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    this.isVisible = true;
  }

  /**
   * 更新现有的进度指示器
   * @private
   */
  _updateIndicator(stage, message, progress) {
    const indicator = document.getElementById(this.currentIndicatorId);
    if (!indicator) {
      // 如果指示器不存在，创建新的
      this._createIndicator(stage, message, progress);
      return;
    }

    // 更新图标和颜色
    const iconElement = indicator.querySelector('.progress-icon');
    if (iconElement) {
      iconElement.textContent = stage.icon;
      iconElement.style.color = stage.color;
    }

    // 更新阶段名称
    const stageNameElement = indicator.querySelector('.progress-stage-name');
    if (stageNameElement) {
      stageNameElement.textContent = stage.name;
    }

    // 更新消息
    const messageElement = indicator.querySelector('.progress-message');
    if (messageElement) {
      messageElement.textContent = message;
    }

    // 更新进度条颜色
    const progressFill = indicator.querySelector('.progress-bar-fill');
    if (progressFill) {
      progressFill.style.backgroundColor = stage.color;
    }

    // 更新spinner颜色
    const spinner = indicator.querySelector('.spinner-ring');
    if (spinner) {
      spinner.style.borderTopColor = stage.color;
    }

    // 更新进度
    if (progress !== null) {
      this.updateProgress(progress);
    }
  }
}

/**
 * 显示友好的错误消息
 * @param {string} error - 错误信息
 * @param {Object} options - 选项
 */
function showFriendlyError(error, options = {}) {
  const {
    showSuggestions = true,
    showRetryButton = false,
    retryAction = null
  } = options;
  
  // 错误消息映射
  const errorMessages = {
    'network': {
      title: '网络连接异常',
      message: '请检查您的网络连接后重试',
      suggestions: [
        '检查网络连接是否正常',
        '尝试刷新页面',
        '如果问题持续，请联系技术支持'
      ]
    },
    'timeout': {
      title: '请求超时',
      message: '服务器响应时间过长，请稍后重试',
      suggestions: [
        '请稍等片刻后重试',
        '检查上传文件大小是否过大',
        '尝试分批处理文件'
      ]
    },
    'file_format': {
      title: '文件格式错误',
      message: '上传的文件格式不正确或文件已损坏',
      suggestions: [
        '请确保上传的是有效的XML文件',
        '检查文件是否完整，没有损坏',
        '尝试重新生成或获取文件'
      ]
    },
    'session_expired': {
      title: '会话已过期',
      message: '当前会话已过期，请重新开始',
      suggestions: [
        '点击"开始生成"按钮重新开始',
        '重新上传文件',
        '如需帮助，请查看使用说明'
      ]
    }
  };
  
  // 根据错误内容匹配错误类型
  let errorType = 'unknown';
  const errorLower = error.toLowerCase();
  
  if (errorLower.includes('网络') || errorLower.includes('network')) {
    errorType = 'network';
  } else if (errorLower.includes('超时') || errorLower.includes('timeout')) {
    errorType = 'timeout';
  } else if (errorLower.includes('xml') || errorLower.includes('格式')) {
    errorType = 'file_format';
  } else if (errorLower.includes('会话') || errorLower.includes('session')) {
    errorType = 'session_expired';
  }
  
  const errorInfo = errorMessages[errorType] || {
    title: '操作失败',
    message: error,
    suggestions: ['请稍后重试', '如果问题持续，请联系技术支持']
  };
  
  let errorHtml = `
    <div class="error-message">
      <div class="error-header">
        <div class="error-icon">⚠️</div>
        <div class="error-title">${errorInfo.title}</div>
      </div>
      <div class="error-content">${errorInfo.message}</div>
  `;
  
  if (showSuggestions && errorInfo.suggestions) {
    errorHtml += `
      <div class="error-suggestions">
        <div class="suggestions-title">建议解决方案：</div>
        <ul class="suggestions-list">
          ${errorInfo.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
        </ul>
      </div>
    `;
  }
  
  errorHtml += `</div>`;
  
  addMessage(errorHtml, "ai");
}

/**
 * 处理生成按钮点击事件
 * 统一的生成按钮响应处理方法
 */
async function handleGenerateClick(buttonElement) {
  try {
    // 防止重复点击
    if (buttonElement.disabled || isGenerating) {
      console.log('⚠️ 按钮已禁用或正在生成中，忽略点击');
      return;
    }
    
    console.log('✅ 开始处理生成按钮点击');
    
    // 禁用按钮并更新状态
    buttonElement.disabled = true;
    const originalText = buttonElement.textContent;
    buttonElement.textContent = "生成中...";
    
    // 添加加载状态指示
    buttonElement.classList.add('loading');
    
    try {
      await startGeneratingCases();
    } catch (error) {
      console.error('生成失败:', error);
      
      // 显示用户友好的错误消息
      let userMessage = "生成失败，请稍后重试。";
      
      if (error.message.includes('会话')) {
        userMessage = "会话已过期，请重新开始对话。";
      } else if (error.message.includes('网络')) {
        userMessage = "网络连接异常，请检查网络后重试。";
      } else if (error.message.includes('409')) {
        userMessage = "系统繁忙，请稍等片刻后重试。";
      }
      
      addMessage(userMessage, "ai");
      
      // 恢复按钮状态
      buttonElement.disabled = false;
      buttonElement.textContent = originalText;
      buttonElement.classList.remove('loading');
      
      // 重置生成状态
      resetGeneratingState();
    }
    
  } catch (error) {
    console.error('处理生成按钮点击失败:', error);
    addMessage("系统异常，请刷新页面后重试。", "ai");
  }
}

/**
 * 优化的流式响应处理
 * 改进错误处理和进度反馈
 */
async function handleStreamResponse(response, progressFill, progressPercent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let lastProgressUpdate = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        console.log('📄 流式响应读取完成');
        break;
      }
      
      buffer += decoder.decode(value, { stream: true });
      
      // 处理完整的数据行
      const lines = buffer.split('\n');
      buffer = lines.pop(); // 保留不完整的行
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            console.log('📊 收到数据:', data);
            
            if (data.type === 'progress') {
              // 优化进度更新，避免过于频繁的DOM操作
              const progressValue = data.data.progress || 0;
              const now = Date.now();
              
              if (now - lastProgressUpdate > 100 || progressValue === 100) { // 限制更新频率
                if (progressFill && progressPercent) {
                  progressFill.style.width = progressValue + "%";
                  progressPercent.textContent = progressValue + "%";
                  console.log('📈 进度更新:', progressValue + '%');
                }
                lastProgressUpdate = now;
              }
              
              // 显示进度相关的状态消息
              if (data.data.status) {
                console.log('📝 状态更新:', data.data.status);
              }
              
            } else if (data.type === 'complete') {
              // 生成完成
              console.log('🎉 生成完成');
              
              if (progressFill && progressPercent) {
                progressFill.style.width = "100%";
                progressPercent.textContent = "100%";
              }
              
              // 存储生成的测试用例
              testCases = data.data.test_cases || [];
              console.log('📋 测试用例数量:', testCases.length);
              
              // 验证测试用例数据完整性
              if (testCases.length === 0) {
                console.warn('⚠️ 生成的测试用例为空');
                addMessage("生成完成，但未生成任何测试用例。请检查输入文件格式。", "ai");
              } else {
                addTestCaseCard();
                showActionButtons();
              }
              
              return { success: true, testCases };
              
            } else if (data.type === 'error') {
              console.error('❌ 生成过程错误:', data.data.message);
              throw new Error(data.data.message || '生成过程中发生错误');
              
            } else if (data.type === 'warning') {
              // 处理警告消息
              console.warn('⚠️ 生成警告:', data.data.message);
              if (data.data.message) {
                addMessage(`提醒：${data.data.message}`, "ai");
              }
            }
            
          } catch (parseError) {
            console.error('解析流数据失败:', parseError, '原始数据:', line);
            // 不中断流处理，继续处理下一行
          }
        }
      }
    }
    
    return { success: true };
    
  } catch (error) {
    console.error('流式响应处理失败:', error);
    throw error;
  } finally {
    // 确保资源清理
    try {
      reader.releaseLock();
    } catch (e) {
      console.warn('释放reader锁失败:', e);
    }
  }
}

// 发送消息
async function sendMessage() {
  const message = elements.chatInput.value.trim()
  if (!message) return

  if (!currentSessionId) {
    alert("请先开始生成任务")
    return
  }

  addMessage(message, "user")
  elements.chatInput.value = ""

  try {
    // 检查是否支持流式API
    const supportsStreaming = await checkStreamingSupport();
    
    if (supportsStreaming) {
      // 使用流式API
      await handleStreamingChat(message);
    } else {
      // 降级到普通API
      await handleRegularChat(message);
    }
    
  } catch (error) {
    console.error('发送消息失败:', error);
    
    // 特殊处理409冲突错误（会话已完成状态）
    if (error.message && error.message.includes('finalized')) {
      addMessage("当前用例已生成完成，如需生成新用例，请在左侧重新上传用例文件，并点击开始生成按钮。", "ai");
    } else {
      addMessage(`发送消息失败: ${error.message}`, "ai");
    }
  }
}

/**
 * 检查是否支持流式API
 */
async function checkStreamingSupport() {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/streaming/support`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('🔍 流式API支持检查结果:', result);
      return result.supported || false;
    } else {
      console.warn('⚠️ 流式API支持检查失败:', response.status, response.statusText);
    }
  } catch (error) {
    console.log('⚠️ 流式API检查失败，使用普通模式:', error);
  }
  
  return false; // 默认不支持流式
}

/**
 * 处理流式聊天
 */
async function handleStreamingChat(message) {
  console.log('🎬 开始流式聊天处理');
  
  try {
    // 调用流式聊天API
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: message
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // 处理Server-Sent Events
    await handleStreamingResponse(response);
    
  } catch (error) {
    console.error('流式聊天失败:', error);
    
    // 完成当前流式显示
    if (globalStreamingDisplay) {
      globalStreamingDisplay.finishStreaming();
      globalStreamingDisplay = null;
    }
    
    // 显示错误并降级到普通聊天
    console.log('⬇️ 降级到普通聊天模式');
    await handleRegularChat(message);
  }
}

/**
 * 处理流式响应
 */
async function handleStreamingResponse(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        console.log('📄 流式响应读取完成');
        break;
      }
      
      buffer += decoder.decode(value, { stream: true });
      
      // 处理完整的数据行
      const lines = buffer.split('\n');
      buffer = lines.pop(); // 保留不完整的行
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            console.log('📊 收到流式数据:', data);
            
            if (data.type === 'stream_start') {
              // 流式传输开始 - 显示进度提示
              console.log('🎬 流式传输开始');
              
            } else if (data.type === 'progress') {
              // 进度更新 - 可以显示进度指示器
              const stage = data.data.stage;
              const message = data.data.message;
              console.log(`📈 进度更新: ${stage} - ${message}`);
              
              // 如果还没有创建流式显示，在这里创建
              if (!globalStreamingDisplay && stage === 'streaming') {
                globalStreamingDisplay = createStreamingMessage();
              }
              
            } else if (data.type === 'streaming' && globalStreamingDisplay) {
              // 追加流式内容
              const content = data.data.content || '';
              if (content) {
                globalStreamingDisplay.appendText(content);
              }
              
            } else if (data.type === 'complete') {
              // 流式传输完成
              console.log('🎉 流式传输完成');
              
              if (globalStreamingDisplay) {
                // 确保显示完整内容
                const fullContent = data.data.content;
                if (fullContent && globalStreamingDisplay.currentText !== fullContent) {
                  // 如果有完整内容且与当前显示不一致，更新为完整内容
                  globalStreamingDisplay.currentText = fullContent;
                  globalStreamingDisplay.displayedText = fullContent;
                  globalStreamingDisplay._updateMessageContent();
                }
                
                globalStreamingDisplay.finishStreaming();
                globalStreamingDisplay = null;
              }
              
              // 检查是否准备好生成
              const shouldShowButton = data.data.ready_to_generate || false;
              if (shouldShowButton) {
                setTimeout(() => {
                  showGenerateButton();
                }, 500);
              }
              
              return;
              
            } else if (data.type === 'stream_complete') {
              // 流式会话完成
              console.log('✅ 流式会话完成');
              
              if (globalStreamingDisplay) {
                globalStreamingDisplay.finishStreaming();
                globalStreamingDisplay = null;
              }
              
              return;
              
            } else if (data.type === 'error') {
              console.error('❌ 流式传输错误:', data.data.message);
              
              // 显示用户友好的错误消息
              const userMessage = data.data.user_message || data.data.message || '流式传输中发生错误';
              
              if (globalStreamingDisplay) {
                globalStreamingDisplay.finishStreaming();
                globalStreamingDisplay = null;
              }
              
              // 显示错误消息
              addMessage(userMessage, "ai");
              
              throw new Error(data.data.message || '流式传输中发生错误');
            }
            
          } catch (parseError) {
            console.error('解析流数据失败:', parseError, '原始数据:', line);
          }
        }
      }
    }
    
  } catch (error) {
    console.error('流式响应处理失败:', error);
    throw error;
  } finally {
    // 确保资源清理
    try {
      reader.releaseLock();
    } catch (e) {
      console.warn('释放reader锁失败:', e);
    }
    
    // 完成流式显示
    if (globalStreamingDisplay) {
      globalStreamingDisplay.finishStreaming();
      globalStreamingDisplay = null;
    }
  }
}

/**
 * 处理普通聊天（降级模式）
 */
async function handleRegularChat(message) {
  // 调用普通聊天API
  const response = await fetch(`${API_BASE_URL}/chat/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: currentSessionId,
      message: message
    })
  });

  const result = await response.json();
  
  if (result.success) {
    // 使用流式效果显示AI回复
    addMessage(result.message, "ai", null, true);
    
    // 检查是否准备好生成
    const message = result.message.toLowerCase();
    const generateKeywords = ['开始生成', '可以生成', '可以开始生成', '准备生成', '现在可以生成'];
    const shouldShowButton = result.ready_to_generate || generateKeywords.some(keyword => message.includes(keyword));
    
    if (shouldShowButton) {
      setTimeout(() => {
        showGenerateButton();
      }, 500);
    }
  } else {
    throw new Error(result.message || '发送消息失败');
  }
}

// 自动发送"开始生成"消息来设置后端状态
async function autoTriggerGeneration() {
  console.log('🤖 自动发送"开始生成"消息来设置后端状态');
  
  if (!currentSessionId) {
    console.error('❌ 会话ID不存在');
    return false;
  }

  try {
    // 发送包含关键词的消息
    const response = await fetch(`${API_BASE_URL}/chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: "开始生成"
      })
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('✅ 后端状态设置成功:', result.ready_to_generate);
      
      // 不显示这个自动消息和AI回复，保持界面简洁
      return result.ready_to_generate;
    } else {
      console.error('❌ 设置后端状态失败:', result.message);
      return false;
    }
    
  } catch (error) {
    console.error('❌ 自动触发生成失败:', error);
    return false;
  }
}

// 重置生成状态
function resetGeneratingState() {
  console.log('🔄 重置生成状态');
  isGenerating = false;
  
  // 恢复左侧主生成按钮状态
  if (elements.generateBtn) {
    elements.generateBtn.disabled = false;
    elements.generateBtn.textContent = "开始生成";
  }
  
  // 恢复聊天中的动态生成按钮状态（处理所有可能的按钮ID）
  const dynamicBtns = document.querySelectorAll('#startGenerateBtn, [id^="startGenerateBtn_"]');
  dynamicBtns.forEach(btn => {
    btn.disabled = false;
    btn.textContent = "开始生成测试用例";
  });
}

// 显示生成按钮
async function showGenerateButton() {
  console.log('🔄 showGenerateButton 被调用');
  
  // 注意：不要重置左侧主按钮状态，因为整个生成流程还没有完成
  // 只重置isGenerating状态，允许聊天中的按钮工作
  isGenerating = false;
  
  // 检查必要的元素是否存在
  if (!elements.chatMessages) {
    console.error('chatMessages 元素不存在，尝试重新获取');
    elements.chatMessages = document.getElementById("chatMessages");
    if (!elements.chatMessages) {
      console.error('无法找到 chatMessages 元素');
      alert('错误：无法找到聊天区域元素');
      return;
    }
  }
  
  // 先确保后端状态正确
  console.log('🔄 检查并设置后端状态...');
  
  const backendReady = await autoTriggerGeneration();
  if (!backendReady) {
    console.error('❌ 后端状态设置失败');
    addMessage("抱歉，系统状态异常，请重新开始对话。", "ai");
    return;
  }
  
  console.log('✅ 后端状态设置成功，显示按钮');
  
  // 生成唯一的按钮ID，避免重复ID问题
  const buttonId = `startGenerateBtn_${Date.now()}`;
  
  // 创建按钮HTML，只使用addEventListener，不使用onclick
  const buttonHtml = `
    <div class="generate-action">
      <button class="action-btn primary" id="${buttonId}">开始生成测试用例</button>
    </div>
  `;
  
  const messageDiv = document.createElement("div");
  messageDiv.className = "message ai-message";
  messageDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">${buttonHtml}</div>
  `;
  
  elements.chatMessages.appendChild(messageDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

  // 获取按钮元素并绑定单一事件监听器
  const startBtn = document.getElementById(buttonId);
  
  if (startBtn) {
    console.log('按钮元素存在，绑定事件监听器');
    
    startBtn.addEventListener('click', async function(event) {
      console.log('🎯 按钮被点击');
      
      event.preventDefault();
      event.stopPropagation();
      
      // 使用统一的按钮处理方法
      await handleGenerateClick(this);
    });
    
    console.log('✅ 按钮事件绑定完成');
    
  } else {
    console.error('❌ 未找到按钮元素!');
    alert('错误：未找到按钮元素');
  }
}

// 开始生成用例
async function startGeneratingCases() {
  console.log('🚀 startGeneratingCases 函数被调用');
  
  console.log('📊 当前状态检查:');
  console.log('  - currentSessionId:', currentSessionId);
  console.log('  - isGenerating:', isGenerating);
  console.log('  - API_BASE_URL:', API_BASE_URL);
  
  if (!currentSessionId) {
    console.error('❌ 会话ID不存在');
    alert("会话已过期，请重新开始");
    return;
  }

  // 防止重复执行
  if (isGenerating) {
    console.log('⚠️ 已经在生成中，忽略请求');
    return;
  }

  // 设置生成状态
  console.log('✅ 设置生成状态为 true');
  isGenerating = true;

  addMessage("好的，开始生成测试用例，请稍候...", "ai");

  progressCounter++;
  const progressId = `generateProgress_${progressCounter}`;
  const progressFillId = `progressFill_${progressCounter}`;
  const progressPercentId = `progressPercent_${progressCounter}`;

  // 添加进度显示
  const progressHtml = `
    <div class="progress-container" id="${progressId}">
      <div class="progress-text">正在生成测试用例... <span id="${progressPercentId}">0%</span></div>
      <div class="progress-bar">
        <div class="progress-fill" id="${progressFillId}" style="width: 0%"></div>
      </div>
    </div>
  `;
  const progressDiv = document.createElement("div");
  progressDiv.className = "message ai-message";
  progressDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">${progressHtml}</div>
  `;
  elements.chatMessages.appendChild(progressDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

  const progressFill = document.getElementById(progressFillId);
  const progressPercent = document.getElementById(progressPercentId);

  console.log('📡 准备发送API请求');

  try {
    // 调用生成API
    console.log('🌐 发送请求到:', `${API_BASE_URL}/generation/generate`);
    const response = await fetch(`${API_BASE_URL}/generation/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: currentSessionId
      })
    });

    console.log('📥 收到响应:', response.status, response.statusText);

    if (!response.ok) {
      // 更详细的错误处理
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.message) {
          errorMessage = errorData.message;
        }
        
        // 特殊处理409冲突错误
        if (response.status === 409) {
          errorMessage = "会话状态不正确，请稍等片刻后重试，或重新开始对话。";
        }
      } catch (e) {
        // 如果无法解析错误响应，使用默认错误信息
        if (response.status === 409) {
          errorMessage = "会话状态冲突，请稍等片刻后重试。";
        }
      }
      
      console.error('❌ API请求失败:', errorMessage);
      throw new Error(errorMessage);
    }

    console.log('✅ API请求成功，开始处理流式响应');

    // 使用优化的流式响应处理
    await handleStreamResponse(response, progressFill, progressPercent);
    
  } catch (error) {
    console.error('生成测试用例失败:', error);
    addMessage(`生成失败: ${error.message}`, "ai");
    
    // 恢复UI状态
    resetGeneratingState();
  }
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

function addMessage(text, type, timestamp = null, streaming = false) {
  const messageTimestamp = timestamp || new Date();
  const formattedTime = formatTimestamp(messageTimestamp);
  
  if (streaming && type === "ai") {
    // 使用流式显示 - 支持真正的流式数据接收
    const streamingDisplay = new StreamingMessageDisplay("chatMessages", {
      typingSpeed: 50,
      cursorBlinkRate: 500,
      autoScroll: true,
      showCursor: true,
      allowSkip: true
    });
    
    const messageId = streamingDisplay.startStreaming();
    
    // 立即开始显示文本
    streamingDisplay.appendText(text);
    
    // 延迟完成，模拟流式效果
    setTimeout(() => {
      streamingDisplay.finishStreaming();
    }, text.length * (1000 / 50) + 500); // 根据文本长度计算显示时间
    
    return messageId;
  } else {
    // 普通消息显示
    const messageDiv = document.createElement("div")
    messageDiv.className = `message ${type}-message`
    messageDiv.innerHTML = `
      <div class="message-avatar">${type === "ai" ? "Agent" : "我"}</div>
      <div class="message-content">
        <div class="message-text">${text.replace(/\n/g, "<br>")}</div>
        <div class="message-timestamp">${formattedTime}</div>
      </div>
    `
    elements.chatMessages.appendChild(messageDiv)
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight
    
    return null;
  }
}

/**
 * 创建流式消息容器 - 用于真正的流式数据接收
 * @param {string} messageId - 消息ID
 * @param {Date} timestamp - 时间戳
 * @returns {StreamingMessageDisplay} 流式显示实例
 */
function createStreamingMessage(messageId = null, timestamp = null) {
  const messageTimestamp = timestamp || new Date();
  const formattedTime = formatTimestamp(messageTimestamp);
  
  // 创建流式显示实例
  const streamingDisplay = new StreamingMessageDisplay("chatMessages", {
    typingSpeed: 60,        // 稍快的显示速度
    cursorBlinkRate: 500,
    autoScroll: true,
    showCursor: true,
    allowSkip: true
  });
  
  // 开始流式显示
  const actualMessageId = streamingDisplay.startStreaming(messageId);
  
  // 添加时间戳到消息容器
  setTimeout(() => {
    const messageElement = document.getElementById(actualMessageId);
    if (messageElement) {
      const messageContent = messageElement.closest('.message-content');
      if (messageContent && !messageContent.querySelector('.message-timestamp')) {
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.textContent = formattedTime;
        messageContent.appendChild(timestampDiv);
      }
    }
  }, 100);
  
  return streamingDisplay;
}

function showActionButtons() {
  generationComplete = true
  isGenerating = false  // 重置生成状态
  elements.chatActionButtons.style.display = "flex"
  elements.continueGenerateBtn.style.display = "inline-flex"
  elements.downloadBtn.style.display = "none"
  elements.chatInputArea.classList.add("hidden")
  
  // 恢复生成按钮状态
  elements.generateBtn.disabled = false
  elements.generateBtn.textContent = "开始生成"
}

function hideActionButtons() {
  generationComplete = false
  elements.chatActionButtons.style.display = "none"
  elements.continueGenerateBtn.style.display = "none"
  elements.downloadBtn.style.display = "none"
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

  if (!currentSessionId) {
    alert("会话已过期，请重新开始");
    return;
  }

  // 先隐藏所有按钮
  elements.chatActionButtons.style.display = "none"
  elements.chatInputArea.classList.add("hidden")

  addMessage("好的，正在基于当前用例继续生成...", "ai")

  progressCounter++
  const progressId = `continueProgress_${progressCounter}`
  const progressFillId = `continueProgressFill_${progressCounter}`
  const progressPercentId = `continueProgressPercent_${progressCounter}`

  // 添加进度显示
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
    <div class="message-content">${progressHtml}</div>
  `
  elements.chatMessages.appendChild(progressDiv)
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight

  const progressFill = document.getElementById(progressFillId)
  const progressPercent = document.getElementById(progressPercentId)

  try {
    // 调用确认生成API
    const response = await fetch(`${API_BASE_URL}/generation/finalize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: currentSessionId,
        test_cases: testCases
      })
    });

    const result = await response.json();
    
    if (result.success) {
      currentFileId = result.file_id;
      
      // 模拟进度更新
      for (let i = 0; i <= 100; i += 5) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        if (progressFill && progressPercent) {
          progressFill.style.width = i + "%";
          progressPercent.textContent = i + "%";
        }
      }

      addMessage("用例文件生成完成！", "ai");

      // 添加下载卡片到聊天界面
      addDownloadCard();

      // 更新所有生成按钮状态为完成状态
      updateAllGenerateButtonsToCompleted();

      // 保持聊天输入可用，不显示单独的下载按钮
      elements.chatInputArea.classList.remove("hidden");
      elements.chatActionButtons.style.display = "none";
    } else {
      throw new Error(result.message || '生成最终文件失败');
    }
    
  } catch (error) {
    console.error('确认生成失败:', error);
    addMessage(`生成失败: ${error.message}`, "ai");
    
    // 恢复按钮状态
    elements.chatActionButtons.style.display = "flex";
    elements.continueGenerateBtn.style.display = "inline-flex";
    elements.downloadBtn.style.display = "none";
  }
}

function downloadFile() {
  if (!currentSessionId || !currentFileId) {
    // 显示错误消息到聊天界面而不是alert
    addMessage("下载信息不完整，请重新生成用例文件。", "ai");
    return;
  }

  try {
    // 构建下载URL
    const downloadUrl = `${API_BASE_URL}/generation/download?session_id=${currentSessionId}&file_id=${currentFileId}`;
    
    // 创建隐藏的下载链接
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = `test_cases_${new Date().toISOString().slice(0, 10)}.xml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // 不在这里添加消息，因为handleDownloadClick会调用showDownloadFeedback
  } catch (error) {
    console.error('下载失败:', error);
    addMessage("下载失败，请稍后重试。", "ai");
  }
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
  alert("保存成功！")
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
    container.innerHTML = `<p class="empty-hint">暂无${hintText}，点击上方按钮添加</p>`
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
                <button class="icon-btn danger delete-comp-btn" data-section="${sectionType}" data-step-index="${stepIndex}" data-comp-index="${compIndex}" title="删除">
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
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      if (confirm("确定要删除吗？")) {
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
    btn.addEventListener("click", (e) => {
      e.stopPropagation()
      if (confirm("确定要删除此组件吗？")) {
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
    alert("请输入名称")
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

// 组件编辑
function openComponentEdit(stepIndex, compIndex, section) {
  editingStepIndex = stepIndex
  editingComponentIndex = compIndex
  editingSection = section
  selectedPresetComponent = null // 重置选中的预设组件

  if (compIndex !== null) {
    const comp = testCases[currentCaseIndex][section][stepIndex].components[compIndex]
    elements.componentEditTitle.textContent = "编辑组件"
    const presetComp = presetComponents.find((p) => p.type === comp.type)
    elements.componentTypeSelect.value = presetComp ? presetComp.name : comp.type
    elements.componentNameInput.value = comp.name
    elements.componentParamsInput.value = JSON.stringify(comp.params, null, 2)
  } else {
    elements.componentEditTitle.textContent = "添加组件"
    elements.componentTypeSelect.value = ""
    elements.componentNameInput.value = ""
    elements.componentParamsInput.value = "{}"
  }

  elements.componentEditOverlay.classList.add("active")
}

function closeComponentEdit() {
  elements.componentEditOverlay.classList.remove("active")
  editingStepIndex = null
  editingComponentIndex = null
  editingSection = null
}

function saveComponent() {
  const funcDesc = elements.componentNameInput.value.trim()
  if (!funcDesc) {
    alert("请输入组件功能描述")
    return
  }

  const compNameValue = elements.componentTypeSelect.value.trim()
  if (!compNameValue) {
    alert("请选择组件名称")
    return
  }

  // 查找对应的组件类型
  let compType = "input" // 默认类型
  const presetComp = presetComponents.find((p) => p.name === compNameValue)
  if (presetComp) {
    compType = presetComp.type
  } else if (selectedPresetComponent) {
    compType = selectedPresetComponent.type
  }

  let params
  try {
    params = JSON.parse(elements.componentParamsInput.value)
  } catch (e) {
    alert("参数格式错误，请输入有效的 JSON")
    return
  }

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

  closeComponentEdit()
  renderCaseDetail()
}

function initSearchableSelect(input, dropdown, options, renderFn, onSelectFn) {
  // 输入框获取焦点时显示下拉框
  input.addEventListener("focus", () => {
    renderDropdownOptions(dropdown, options, input.value, renderFn, onSelectFn)
    dropdown.classList.add("show")
  })

  // 输入时过滤选项
  input.addEventListener("input", () => {
    renderDropdownOptions(dropdown, options, input.value, renderFn, onSelectFn)
    dropdown.classList.add("show")
  })

  // 点击外部关闭下拉框
  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove("show")
    }
  })
}

function renderDropdownOptions(dropdown, options, searchText, renderFn, onSelectFn) {
  const filtered = options.filter(
    (opt) =>
      opt.name.toLowerCase().includes(searchText.toLowerCase()) ||
      (opt.description && opt.description.toLowerCase().includes(searchText.toLowerCase())),
  )

  if (filtered.length === 0) {
    dropdown.innerHTML = '<div class="no-results">无匹配结果，可直接输入自定义名称</div>'
    return
  }

  dropdown.innerHTML = filtered.map((opt) => renderFn(opt)).join("")

  // 绑定点击事件
  dropdown.querySelectorAll(".select-option").forEach((el, index) => {
    el.addEventListener("click", () => {
      onSelectFn(filtered[index])
      dropdown.classList.remove("show")
    })
  })
}

function renderStepOption(step) {
  const componentCount = step.components ? step.components.length : 0
  return `
    <div class="select-option" data-id="${step.id}">
      <div class="select-option-name">${step.name}</div>
      <div class="select-option-desc">${step.description || ""}</div>
      <div class="select-option-components">包含 ${componentCount} 个预设组件</div>
    </div>
  `
}

function renderComponentOption(comp) {
  const iconSvg = getComponentIcon(comp.icon)
  return `
    <div class="select-option" data-id="${comp.id}">
      <div class="component-option">
        <div class="component-option-icon">${iconSvg}</div>
        <div class="component-option-info">
          <div class="component-option-name">${comp.name}</div>
          <div class="component-option-type">${comp.description}</div>
        </div>
      </div>
    </div>
  `
}

function getComponentIcon(iconName) {
  const icons = {
    edit: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>',
    pointer:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>',
    list: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
    "check-square":
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>',
    globe:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>',
    "check-circle":
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
    clock:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
    "arrow-down":
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>',
    upload:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>',
    camera:
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>',
  }
  return icons[iconName] || icons.edit
}

function onStepSelected(step) {
  selectedPresetStep = step
  elements.stepNameInput.value = step.name
  elements.stepDescInput.value = step.description || ""
}

function onComponentSelected(comp) {
  selectedPresetComponent = comp
  elements.componentTypeSelect.value = comp.name
  // 加载该组件类型的默认参数
  const defaultParams = componentDefaultParams[comp.type] || {}
  elements.componentParamsInput.value = JSON.stringify(defaultParams, null, 2)
}

// 注意：init() 函数已经在 initializeApp() 中调用，不需要在这里重复调用

// 说明面板折叠功能
function toggleInstructions() {
  instructionsExpanded = !instructionsExpanded;
  updateInstructionsState();
}

function initializeInstructionsState() {
  // 设置默认折叠状态
  instructionsExpanded = false;
  updateInstructionsState();
}

function updateInstructionsState() {
  if (elements.instructionsCard && elements.instructionsHeader && elements.instructionsContent) {
    if (instructionsExpanded) {
      elements.instructionsCard.classList.remove('collapsed');
      elements.instructionsHeader.setAttribute('aria-expanded', 'true');
      elements.instructionsContent.setAttribute('aria-hidden', 'false');
    } else {
      elements.instructionsCard.classList.add('collapsed');
      elements.instructionsHeader.setAttribute('aria-expanded', 'false');
      elements.instructionsContent.setAttribute('aria-hidden', 'true');
    }
  }
}

// 键盘支持
function handleInstructionsKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    toggleInstructions();
  }
}
// 对话持久化相关函数
function addSessionSeparator() {
  const separatorDiv = document.createElement("div");
  separatorDiv.className = "session-separator";
  separatorDiv.innerHTML = `
    <div class="separator-line"></div>
    <div class="separator-text">新会话开始</div>
    <div class="separator-line"></div>
  `;
  elements.chatMessages.appendChild(separatorDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function clearConversation() {
  // 可选的完全清空对话功能
  elements.chatMessages.innerHTML = '';
  isFirstGeneration = true;
}
// 下载卡片相关函数
function createDownloadCard(fileName = null, fileSize = null) {
  const defaultFileName = fileName || `test_cases_${new Date().toISOString().slice(0, 10)}.xml`;
  const defaultFileSize = fileSize || "2.3 KB";
  
  const downloadCardHtml = `
    <div class="download-card" id="downloadCard" role="region" aria-label="文件下载卡片">
      <div class="download-card-header">
        <div class="download-icon" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
        </div>
        <div class="download-info">
          <h4 id="download-title">测试用例文件已生成</h4>
          <span class="file-details" aria-describedby="download-title">${defaultFileName} (${defaultFileSize})</span>
        </div>
      </div>
      <button class="download-button" id="downloadFileBtn" 
              aria-label="下载测试用例文件 ${defaultFileName}" 
              title="点击下载 ${defaultFileName}">
        <svg class="download-btn-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        <span>下载文件</span>
      </button>
    </div>
  `;
  
  return downloadCardHtml;
}

function addDownloadCard(fileName = null, fileSize = null) {
  const cardHtml = createDownloadCard(fileName, fileSize);
  
  const messageDiv = document.createElement("div");
  messageDiv.className = "message ai-message";
  messageDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">
      <div class="message-text">用例文件生成完成！点击下方卡片下载文件。</div>
      <div class="message-timestamp">${formatTimestamp(new Date())}</div>
      ${cardHtml}
    </div>
  `;
  
  elements.chatMessages.appendChild(messageDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  
  // 绑定下载按钮事件
  const downloadBtn = messageDiv.querySelector('#downloadFileBtn');
  if (downloadBtn) {
    downloadBtn.addEventListener('click', handleDownloadClick);
    downloadBtn.addEventListener('keydown', handleDownloadKeydown);
  }
  
  return messageDiv;
}

function handleDownloadClick() {
  try {
    // 调用原有的下载函数
    downloadFile();
    
    // 显示下载反馈
    showDownloadFeedback();
  } catch (error) {
    console.error('下载卡片点击处理失败:', error);
    addMessage("下载操作失败，请稍后重试。", "ai");
  }
}

function handleDownloadKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    handleDownloadClick();
  }
}

function showDownloadFeedback() {
  // 临时显示下载反馈消息
  const feedbackDiv = document.createElement("div");
  feedbackDiv.className = "message ai-message";
  feedbackDiv.innerHTML = `
    <div class="message-avatar">Agent</div>
    <div class="message-content">
      <div class="message-text">文件下载已开始！</div>
      <div class="message-timestamp">${formatTimestamp(new Date())}</div>
    </div>
  `;
  
  elements.chatMessages.appendChild(feedbackDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}