"""
Flask后端API服务
提供测试用例生成工具所需的mock数据接口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ============ Mock数据定义 ============

# 1. 历史用例案例库选项
CASE_LIBRARY_OPTIONS = [
    {"value": "all", "label": "全量历史用例案例库"},
    {"value": "archived", "label": "已归档精品案例库"}
]

# 组件默认参数配置
COMPONENT_DEFAULT_PARAMS = {
    "phone": {
        "callingId": "",
        "calledId": "",
        "callingVisit": "",
        "calledVisit": "",
        "forwardId": "",
        "forwardVisit": ""
    },
    "variable": {
        "vars": ""
    },
    "saveUserInfo": {
        "comments": "",
        "rTpl": "@\\saveuserinfo\\SaveUserInfo.xml",
        "rReq": "<Save DefaultValue=\"\" Idx=\"1\"/>;"
    },
    "moveForwardEfftime": {
        "comments": "",
        "env": "${Env}",
        "number": "${My_SubIdentity}",
        "groupkey": "",
        "forwardhours": ""
    },
    "delayTime": {
        "comments": "",
        "delaytimes": ""
    },
    "database": {
        "comments": "",
        "dbUrl": "",
        "env": "${Env}",
        "conditiontype": "",
        "condition": "",
        "dbtype": "",
        "sql": "",
        "tableName": "",
        "operation": "",
        "values": "",
        "conditions": "",
        "vars": "",
        "types": "",
        "extendConditions": "",
        "retryTimes": "",
        "timeout": "",
        "checkAmount": ""
    },
    "api": {
        "rTpl": "@\\soap\\Request.xml",
        "url": "${Env.BMPAPP101.SoapUrl}",
        "tenantId": "${My_tenantId}",
        "rReq": {
            "header": {
                "version": {"type": "string", "value": "1.0"},
                "bizCode": {"type": "string", "value": "CREATE_SUBSCRIBER"},
                "transId": {"type": "string", "value": "${G.uuid()}"},
                "timestamp": {"type": "string", "value": "${G.now()}"}
            },
            "body": {
                "subscriberInfo": {
                    "msisdn": {"type": "string", "value": "${My_SubIdentity}"},
                    "imsi": {"type": "string", "value": "${My_IMSI}"},
                    "status": {"type": "number", "value": 1},
                    "createDate": {"type": "date", "value": "${G.today()}"}
                },
                "offeringInfo": {
                    "primaryOfferingId": {"type": "string", "value": "${My_PrimaryOfferingID}"},
                    "effectiveDate": {"type": "date", "value": "${G.today()}"}
                }
            }
        },
        "rRsp": {
            "resultCode": {"type": "string", "value": "0", "validation": "equals"},
            "resultMsg": {"type": "string", "value": "Success", "validation": "contains"},
            "data": {
                "subscriberId": {"type": "string", "value": "", "validation": "notEmpty", "saveAs": "My_SubscriberId"},
                "accountId": {"type": "string", "value": "", "validation": "notEmpty", "saveAs": "My_AccountId"}
            }
        }
    },
    "comment": {
        "content": ""
    },
    "restful": {
        "rTpl": "@\\rest\\GetUser.json",
        "url": "${Env.RestApiUrl}/api/v1",
        "method": "GET",
        "rReq": {
            "headers": {
                "Content-Type": {"type": "string", "value": "application/json", "isDefault": True},
                "Authorization": {"type": "string", "value": "Bearer ${My_Token}"}
            },
            "body": {
                "userId": {"type": "string", "value": "${My_UserId}"},
                "name": {"type": "string", "value": ""},
                "email": {"type": "string", "value": ""},
                "status": {"type": "number", "value": 1, "isDefault": True}
            }
        },
        "rRsp": {
            "code": {"type": "number", "value": 200, "validation": "equals", "isDefault": True},
            "message": {"type": "string", "value": "success", "validation": "noCare", "isDefault": True},
            "data": {
                "id": {"type": "string", "value": "", "validation": "notEmpty", "saveAs": ""},
                "createdAt": {"type": "date", "value": "", "validation": "noCare"}
            }
        }
    },
    "shell": {
        "url": "",
        "cmd": "",
        "timeout": "",
        "shellChecks": ""
    },
    "task": {
        "planType": "",
        "planName": "",
        "status": "",
        "tenantID": "",
        "timeout": ""
    }
}

# 2. 搜索历史用例的结果数据
MOCK_SEARCH_RESULTS = [
    {
        "id": "HTC001",
        "name": "月度账单生成及计费验证",
        "preconditions": [
            {
                "id": "hp1",
                "name": "初始化用户账户数据",
                "expanded": False,
                "components": [
                    {"id": "hpc1", "type": "database", "name": "数据库查询 - 检查账户状态", "params": {"dbUrl": "${Env.AdminDB}", "sql": "select * from USER_ACCOUNT where status=1", "timeout": "30"}},
                    {"id": "hpc2", "type": "variable", "name": "设置变量 - 账户参数", "params": {"vars": "My_AcctId=123456;My_BillCycle=202501"}}
                ]
            }
        ],
        "steps": [
            {
                "id": "hs1",
                "name": "执行账单计算任务",
                "expanded": True,
                "components": [
                    {"id": "hc1", "type": "task", "name": "任务触发 - 月度账单生成", "params": {"planType": "triggeringTaskPlan", "planName": "Monthly_Bill_Generate", "status": "f", "timeout": "300"}},
                    {"id": "hc2", "type": "delayTime", "name": "时间延迟 - 等待任务完成", "params": {"delaytimes": "60"}}
                ]
            },
            {
                "id": "hs2",
                "name": "验证账单数据准确性",
                "expanded": False,
                "components": [
                    {"id": "hc3", "type": "database", "name": "数据库查询 - 查询账单记录", "params": {"dbUrl": "${Env.DCDB204}", "tableName": "DC_INVOICE_DETAIL", "operation": "Select", "conditions": "ACCT_ID|${My_AcctId}", "timeout": "30"}}
                ]
            }
        ],
        "expectedResults": [
            {
                "id": "he1",
                "name": "账单生成成功且金额正确",
                "expanded": False,
                "components": [
                    {"id": "hec1", "type": "database", "name": "数据库查询 - 验证账单金额", "params": {"dbUrl": "${Env.DCDB204}", "sql": "select count(*) from DC_INVOICE_DETAIL where ACCT_ID=${My_AcctId} and BILL_CYCLE='${My_BillCycle}'", "checkAmount": "1"}}
                ]
            }
        ]
    },
    {
        "id": "HTC002",
        "name": "用户套餐变更及生效验证",
        "preconditions": [
            {
                "id": "hp2",
                "name": "创建测试用户",
                "expanded": False,
                "components": [
                    {"id": "hpc3", "type": "phone", "name": "号码配置 - 分配号码", "params": {"callingId": "Native_HD_C1A1_Onnet", "callingVisit": "C1A1", "calledId": "Native_HD_C1A1_Onnet", "calledVisit": "C1A1"}},
                    {"id": "hpc4", "type": "api", "name": "SOAP接口调用 - 创建用户", "params": {"rTpl": "@\\soap\\CreateSubscriber.xml", "url": "${Env.BMPAPP101.SoapUrl}", "tenantId": "${My_tenantId}"}}
                ]
            }
        ],
        "steps": [
            {
                "id": "hs4",
                "name": "执行套餐变更操作",
                "expanded": False,
                "components": [
                    {"id": "hc4", "type": "variable", "name": "设置变量 - 变更套餐参数", "params": {"vars": "My_NewOfferingID=${Offer_NewPlan.ID};My_EffectiveDate=${G.now()}"}},
                    {"id": "hc5", "type": "api", "name": "SOAP接口调用 - 套餐变更", "params": {"rTpl": "@\\soap\\ModifyOffering.xml", "url": "${Env.BMPAPP101.SoapUrl}", "tenantId": "${My_tenantId}"}}
                ]
            },
            {
                "id": "hs5",
                "name": "触发套餐生效处理",
                "expanded": False,
                "components": [
                    {"id": "hc6", "type": "moveForwardEfftime", "name": "时间前移 - 生效时间", "params": {"number": "${My_SubIdentity}", "forwardhours": "24"}}
                ]
            }
        ],
        "expectedResults": [
            {
                "id": "he2",
                "name": "套餐变更成功并已生效",
                "expanded": False,
                "components": [
                    {"id": "hec2", "type": "database", "name": "数据库查询 - 验证套餐状态", "params": {"dbUrl": "${Env.AdminDB}", "tableName": "SUBSCRIBER_OFFERING", "operation": "Select", "conditions": "SUB_ID|${calling.Sub.SUB_ID}", "vars": "OFFERING_ID", "timeout": "30"}},
                    {"id": "hec3", "type": "shell", "name": "Shell执行 - 验证日志", "params": {"url": "${Env.BMPAPP101.sshurl}", "cmd": "grep 'ModifyOffering success' bmp_debug.log |wc -l", "shellChecks": "1"}}
                ]
            }
        ]
    },
    {
        "id": "HTC003",
        "name": "欠费停机及复机流程测试",
        "preconditions": [
            {
                "id": "hp3",
                "name": "创建欠费用户",
                "expanded": False,
                "components": [
                    {"id": "hpc5", "type": "phone", "name": "号码配置 - 分配号码", "params": {"callingId": "Native_HD_C1A1_Onnet", "callingVisit": "C1A1", "calledId": "Native_HD_C1A1_Onnet", "calledVisit": "C1A1"}},
                    {"id": "hpc6", "type": "variable", "name": "设置变量 - 开户参数", "params": {"vars": "My_PrimaryOfferingID=${Offer_ATP_Primary_POS.ID};My_Charge=1000000;My_tenantId=0"}},
                    {"id": "hpc7", "type": "api", "name": "SOAP接口调用 - 创建用户", "params": {"rTpl": "@\\soap\\CreateSubscriber.xml", "url": "${Env.BMPAPP101.SoapUrl}", "tenantId": "${My_tenantId}"}}
                ]
            },
            {
                "id": "hp4",
                "name": "调整账户为欠费状态",
                "expanded": False,
                "components": [
                    {"id": "hpc8", "type": "variable", "name": "设置变量 - 欠费调整参数", "params": {"vars": "My_AdjOpType=1;My_AdjType=2;My_AdjAmt=5000000;My_AdjCurrencyID=1049"}},
                    {"id": "hpc9", "type": "api", "name": "SOAP接口调用 - 欠费调整", "params": {"rTpl": "@\\soap\\Adjustment.xml", "url": "${Env.BMPAPP101.SoapUrl}", "tenantId": "${My_tenantId}"}}
                ]
            }
        ],
        "steps": [
            {
                "id": "hs6",
                "name": "执行停机处理",
                "expanded": False,
                "components": [
                    {"id": "hc7", "type": "task", "name": "任务触发 - 欠费停机任务", "params": {"planType": "triggeringTaskPlan", "planName": "Suspend_Debit_User", "status": "f", "tenantID": "${My_tenantId}", "timeout": "120"}},
                    {"id": "hc8", "type": "delayTime", "name": "时间延迟 - 等待停机完成", "params": {"delaytimes": "30"}}
                ]
            },
            {
                "id": "hs7",
                "name": "充值并执行复机",
                "expanded": False,
                "components": [
                    {"id": "hc9", "type": "variable", "name": "设置变量 - 充值参数", "params": {"vars": "My_PaymentAmt=10000000;My_PaymentMethod=1"}},
                    {"id": "hc10", "type": "api", "name": "SOAP接口调用 - 账户充值", "params": {"rTpl": "@\\soap\\Payment.xml", "url": "${Env.BMPAPP101.SoapUrl}", "tenantId": "${My_tenantId}"}},
                    {"id": "hc11", "type": "task", "name": "任务触发 - 复机任务", "params": {"planType": "triggeringTaskPlan", "planName": "Resume_User_Service", "status": "f", "tenantID": "${My_tenantId}", "timeout": "120"}}
                ]
            }
        ],
        "expectedResults": [
            {
                "id": "he3",
                "name": "用户成功复机且服务正常",
                "expanded": False,
                "components": [
                    {"id": "hec4", "type": "database", "name": "数据库查询 - 验证用户状态", "params": {"dbUrl": "${Env.AdminDB}", "tableName": "SUBSCRIBER", "operation": "Select", "conditions": "SUB_ID|${calling.Sub.SUB_ID}", "vars": "STATUS", "timeout": "30"}},
                    {"id": "hec5", "type": "comment", "name": "步骤注释 - 验证完成", "params": {"content": "用户状态应为Active(1),余额大于0"}}
                ]
            }
        ]
    }
]

# 3. 预置步骤和预置组件数据
PRESET_STEPS = [
    {
        "id": "preset_1",
        "name": "打开登录页面",
        "description": "打开系统登录页面并等待加载完成",
        "components": [
            {"type": "api", "name": "接口调用 - 获取登录页", "params": {"method": "GET", "url": "/login"}},
            {"type": "assert", "name": "断言 - 页面加载完成", "params": {"type": "visible", "selector": "#login-form"}}
        ]
    },
    {
        "id": "preset_2",
        "name": "输入用户凭证",
        "description": "输入用户名和密码",
        "components": [
            {"type": "input", "name": "输入框 - 用户名", "params": {"value": "", "placeholder": "请输入用户名"}},
            {"type": "input", "name": "输入框 - 密码", "params": {"value": "", "encrypted": True}}
        ]
    },
    {
        "id": "preset_3",
        "name": "点击登录按钮",
        "description": "点击登录按钮提交表单",
        "components": [
            {"type": "button", "name": "按钮 - 登录", "params": {"id": "login-btn", "text": "登录"}}
        ]
    }
]

PRESET_COMPONENTS = [
    {"id": "comp_phone", "type": "phone", "name": "号码配置", "alias": "PhonesAssign", "icon": "phone", "description": "设置主被叫号码、呼叫区域和呼叫转移参数"},
    {"id": "comp_variable", "type": "variable", "name": "设置变量", "alias": "TableSetVar", "icon": "variable", "description": "创建并设置变量值、设置请求参数、预置测试数据"},
    {"id": "comp_saveUserInfo", "type": "saveUserInfo", "name": "保存用户信息至变量", "alias": "SaveUserInfo", "icon": "save", "description": "创建用户结束后，获取用户信息，保存至环境变量"},
    {"id": "comp_moveForwardEfftime", "type": "moveForwardEfftime", "name": "时间前移", "alias": "MoveForwardEfftime", "icon": "clock-forward", "description": "时间前移"},
    {"id": "comp_delayTime", "type": "delayTime", "name": "时间延迟", "alias": "DelayTime", "icon": "clock-delay", "description": "执行延迟时间"},
    {"id": "comp_database", "type": "database", "name": "数据库查询", "alias": "DataBaseQuery", "icon": "database", "description": "执行数据库查询数据的操作，查询某个表的某个字段值"},
    {"id": "comp_api", "type": "api", "name": "Soap请求", "alias": "SoapClient", "icon": "globe", "description": "发送Soap请求到指定接口，并校验接口返回数据"},
    {"id": "comp_comment", "type": "comment", "name": "步骤注释", "alias": "comment", "icon": "message-square", "description": "对自动化用例步骤进行注释"},
    {"id": "comp_restful", "type": "restful", "name": "Rest请求", "alias": "RestfulClient", "icon": "send", "description": "发送Rest请求，到接口，接收返回消息并对返回消息进行校验"},
    {"id": "comp_shell", "type": "shell", "name": "Shell执行", "alias": "ShellExec", "icon": "terminal", "description": "执行Shell命令"},
    {"id": "comp_task", "type": "task", "name": "任务触发", "alias": "TaskTrigger", "icon": "play-circle", "description": "触发定时任务执行"}
]

# ============ API接口定义 ============

@app.route('/api/case-library-options', methods=['GET'])
def get_case_library_options():
    """
    接口1: 获取历史用例案例库的下拉选择项
    返回格式: { "success": true, "data": [...] }
    """
    return jsonify({
        "success": True,
        "data": CASE_LIBRARY_OPTIONS
    })


@app.route('/api/search-history-cases', methods=['POST'])
def search_history_cases():
    """
    接口2: 搜索历史用例
    请求参数: {
        "caseLibrary": "all" | "archived",  // 案例库类型
        "searchMethod": "keyword" | "semantic",  // 搜索方式
        "searchText": "用户输入的搜索文本"
    }
    返回格式: { "success": true, "data": [...] }
    """
    data = request.get_json()
    case_library = data.get('caseLibrary', 'all')
    search_method = data.get('searchMethod', 'keyword')
    search_text = data.get('searchText', '')
    
    # Mock逻辑：根据搜索文本简单过滤
    results = MOCK_SEARCH_RESULTS
    if search_text:
        results = [
            case for case in MOCK_SEARCH_RESULTS 
            if search_text.lower() in case['name'].lower()
        ]
    
    return jsonify({
        "success": True,
        "data": results,
        "filters": {
            "caseLibrary": case_library,
            "searchMethod": search_method,
            "searchText": search_text
        }
    })


@app.route('/api/preset-data', methods=['GET'])
def get_preset_data():
    """
    接口3: 获取预置步骤和预置组件数据
    返回格式: { 
        "success": true, 
        "data": {
            "steps": [...],
            "components": [...]
        }
    }
    """
    return jsonify({
        "success": True,
        "data": {
            "steps": PRESET_STEPS,
            "components": PRESET_COMPONENTS,
            "componentDefaultParams": COMPONENT_DEFAULT_PARAMS
        }
    })


@app.route('/api/param-schemas', methods=['GET'])
def get_param_schemas():
    """
    接口4: 获取组件参数配置架构
    返回格式: { 
        "success": true, 
        "data": {
            "phone": [...],
            "variable": [...],
            ...
        }
    }
    """
    schemas = {
        'phone': [
            {'name': 'callingId', 'label': '主叫号码', 'type': 'combo', 'required': True, 'options': ['Native_HD_C1A1_Onnet', 'Native_HD_C1A2_Onnet', 'Roaming_HD_V1_Onnet']},
            {'name': 'calledId', 'label': '被叫号码', 'type': 'combo', 'required': True, 'options': ['Native_HD_C1A1_Onnet', 'Native_HD_C1A2_Onnet', 'Roaming_HD_V1_Onnet']},
            {'name': 'callingVisit', 'label': '主叫区域', 'type': 'input', 'required': False},
            {'name': 'calledVisit', 'label': '被叫区域', 'type': 'input', 'required': False},
            {'name': 'forwardId', 'label': '转移号码', 'type': 'input', 'required': False},
            {'name': 'forwardVisit', 'label': '转移区域', 'type': 'input', 'required': False}
        ],
        'variable': [
            {'name': 'vars', 'label': '变量列表', 'type': 'variable-list', 'required': True}
        ],
        'database': [
            {'name': 'dbUrl', 'label': '数据库URL', 'type': 'input', 'required': True, 'placeholder': '${Env.AdminDB}'},
            {'name': 'operation', 'label': '操作类型', 'type': 'combo', 'required': True, 'options': ['Select', 'Insert', 'Update', 'Delete']},
            {'name': 'tableName', 'label': '表名', 'type': 'input', 'required': False},
            {'name': 'sql', 'label': 'SQL语句', 'type': 'textarea', 'required': False},
            {'name': 'conditions', 'label': '查询条件', 'type': 'input', 'required': False, 'placeholder': 'FIELD|VALUE'},
            {'name': 'vars', 'label': '变量', 'type': 'input', 'required': False},
            {'name': 'timeout', 'label': '超时时间(秒)', 'type': 'input', 'required': False, 'placeholder': '30'}
        ],
        'api': [
            {'name': 'rTpl', 'label': '请求模板', 'type': 'template-select', 'required': True, 'options': [
                {'value': '@\\soap\\CreateSubscriber.xml', 'label': '创建用户'},
                {'value': '@\\soap\\QuerySubscriber.xml', 'label': '查询用户'},
                {'value': '@\\soap\\ModifySubscriber.xml', 'label': '修改用户'},
                {'value': '@\\soap\\DeleteSubscriber.xml', 'label': '删除用户'},
                {'value': '@\\soap\\CreateAccount.xml', 'label': '创建账户'},
                {'value': '@\\soap\\Payment.xml', 'label': '缴费'},
                {'value': '@\\soap\\Adjustment.xml', 'label': '调账'},
                {'value': '@\\soap\\ChangeOffering.xml', 'label': '变更套餐'}
            ]},
            {'name': 'url', 'label': '接口URL', 'type': 'input', 'required': True, 'placeholder': '${Env.BMPAPP101.SoapUrl}'},
            {'name': 'tenantId', 'label': '租户ID', 'type': 'input', 'required': False, 'placeholder': '${My_tenantId}'},
            {'name': 'rReq', 'label': '请求参数', 'type': 'json-tree', 'required': False, 'isRequest': True, 'defaultValue': {
                'header': {
                    'version': {'type': 'string', 'value': '1.0', 'isDefault': True},
                    'bizCode': {'type': 'string', 'value': 'CREATE_SUBSCRIBER', 'isDefault': True},
                    'transId': {'type': 'string', 'value': '${G.uuid()}', 'isDefault': True},
                    'timestamp': {'type': 'string', 'value': '${G.now()}', 'isDefault': True}
                },
                'body': {
                    'subscriberInfo': {
                        'msisdn': {'type': 'string', 'value': '${My_SubIdentity}'},
                        'imsi': {'type': 'string', 'value': '${My_IMSI}'},
                        'status': {'type': 'number', 'value': 1, 'isDefault': True},
                        'createDate': {'type': 'date', 'value': '${G.today()}', 'isDefault': True}
                    },
                    'offeringInfo': {
                        'primaryOfferingId': {'type': 'string', 'value': '${My_PrimaryOfferingID}'},
                        'effectiveDate': {'type': 'date', 'value': '${G.today()}', 'isDefault': True}
                    }
                }
            }},
            {'name': 'rRsp', 'label': '响应验证', 'type': 'json-tree', 'required': False, 'isResponse': True, 'defaultValue': {
                'resultCode': {'type': 'string', 'value': '0', 'validation': 'equals', 'isDefault': True},
                'resultMsg': {'type': 'string', 'value': 'Success', 'validation': 'noCare', 'isDefault': True},
                'data': {
                    'subscriberId': {'type': 'string', 'value': '', 'validation': 'notEmpty', 'saveAs': ''},
                    'accountId': {'type': 'string', 'value': '', 'validation': 'notEmpty', 'saveAs': ''}
                }
            }}
        ],
        'task': [
            {'name': 'planType', 'label': '计划类型', 'type': 'combo', 'required': True, 'options': ['triggeringTaskPlan', 'scheduledTaskPlan']},
            {'name': 'planName', 'label': '任务名称', 'type': 'input', 'required': True},
            {'name': 'status', 'label': '状态', 'type': 'combo', 'required': True, 'options': ['f', 's']},
            {'name': 'tenantID', 'label': '租户ID', 'type': 'input', 'required': False, 'placeholder': '${My_tenantId}'},
            {'name': 'timeout', 'label': '超时时间(秒)', 'type': 'input', 'required': False, 'placeholder': '120'}
        ],
        'delayTime': [
            {'name': 'delaytimes', 'label': '延迟时间(秒)', 'type': 'input', 'required': True, 'placeholder': '60'},
            {'name': 'comments', 'label': '备注', 'type': 'input', 'required': False}
        ],
        'moveForwardEfftime': [
            {'name': 'number', 'label': '号码', 'type': 'input', 'required': True, 'placeholder': '${My_SubIdentity}'},
            {'name': 'forwardhours', 'label': '前移小时数', 'type': 'input', 'required': True, 'placeholder': '24'},
            {'name': 'env', 'label': '环境', 'type': 'input', 'required': False, 'placeholder': '${Env}'},
            {'name': 'groupkey', 'label': '组键', 'type': 'input', 'required': False}
        ],
        'shell': [
            {'name': 'url', 'label': 'SSH地址', 'type': 'input', 'required': True, 'placeholder': '${Env.BMPAPP101.sshurl}'},
            {'name': 'cmd', 'label': 'Shell命令', 'type': 'textarea', 'required': True},
            {'name': 'timeout', 'label': '超时时间(秒)', 'type': 'input', 'required': False, 'placeholder': '30'},
            {'name': 'shellChecks', 'label': '校验值', 'type': 'input', 'required': False}
        ],
        'restful': [
            {'name': 'rTpl', 'label': '请求模板', 'type': 'template-select', 'required': True, 'options': [
                {'value': '@\\rest\\GetUser.json', 'label': 'GET 获取用户'},
                {'value': '@\\rest\\CreateUser.json', 'label': 'POST 创建用户'},
                {'value': '@\\rest\\UpdateUser.json', 'label': 'PUT 更新用户'},
                {'value': '@\\rest\\DeleteUser.json', 'label': 'DELETE 删除用户'},
                {'value': '@\\rest\\QueryList.json', 'label': 'GET 查询列表'},
                {'value': '@\\rest\\BatchCreate.json', 'label': 'POST 批量创建'}
            ]},
            {'name': 'url', 'label': '接口URL', 'type': 'input', 'required': True, 'placeholder': '${Env.RestApiUrl}/api/v1'},
            {'name': 'method', 'label': '请求方法', 'type': 'combo', 'required': True, 'options': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']},
            {'name': 'rReq', 'label': '请求参数', 'type': 'json-tree', 'required': False, 'isRequest': True, 'defaultValue': {
                'headers': {
                    'Content-Type': {'type': 'string', 'value': 'application/json', 'isDefault': True},
                    'Authorization': {'type': 'string', 'value': 'Bearer ${My_Token}'}
                },
                'body': {
                    'userId': {'type': 'string', 'value': '${My_UserId}'},
                    'name': {'type': 'string', 'value': ''},
                    'email': {'type': 'string', 'value': ''},
                    'status': {'type': 'number', 'value': 1, 'isDefault': True}
                }
            }},
            {'name': 'rRsp', 'label': '响应验证', 'type': 'json-tree', 'required': False, 'isResponse': True, 'defaultValue': {
                'code': {'type': 'number', 'value': 200, 'validation': 'equals', 'isDefault': True},
                'message': {'type': 'string', 'value': 'success', 'validation': 'noCare', 'isDefault': True},
                'data': {
                    'id': {'type': 'string', 'value': '', 'validation': 'notEmpty', 'saveAs': ''},
                    'createdAt': {'type': 'date', 'value': '', 'validation': 'noCare'}
                }
            }}
        ],
        'comment': [
            {'name': 'content', 'label': '注释内容', 'type': 'textarea', 'required': True}
        ],
        'saveUserInfo': [
            {'name': 'rTpl', 'label': '模板路径', 'type': 'input', 'required': False, 'placeholder': '@\\saveuserinfo\\SaveUserInfo.xml'},
            {'name': 'rReq', 'label': '保存配置', 'type': 'textarea', 'required': False},
            {'name': 'comments', 'label': '备注', 'type': 'input', 'required': False}
        ]
    }
    
    return jsonify({
        "success": True,
        "data": schemas
    })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "Flask API server is running"})


if __name__ == '__main__':
    print("=" * 60)
    print("Flask API服务器启动中...")
    print("服务地址: http://localhost:5000")
    print("=" * 60)
    print("\n可用接口:")
    print("  GET  /api/case-library-options  - 获取案例库选项")
    print("  POST /api/search-history-cases  - 搜索历史用例")
    print("  GET  /api/preset-data           - 获取预置步骤和组件")
    print("  GET  /api/param-schemas         - 获取参数配置架构")
    print("  GET  /health                    - 健康检查")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
