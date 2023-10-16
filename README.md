# jxb-api
基于excel的关键字驱动接口自动化

- 用例使用纯excel进行编写
- 使用pytest + requests实现接口调用
- 使用Dash + plotly 生成网页报告

## 使用方式

### 配置环境
1. 在 `settings.py` 文件中, 修改 `BASE_URL` 基本前缀url信息
### 编写接口文档
1. 在 `url.xlsx` 文件中添加接口信息, 包含接口名称, 接口url, 请求方式和请求参数数据
2. 名称将会在用例的excel文件或者关键字的excel文件中进行使用
3. 请求方式大小写适应
4. 参数列, 可以填写json格式的数据, 也可以填写python中的字典格式数据

### 编写关键字
> 详细使用方式参考后面使用说明
1. 在 `keywords` 文件夹下创建 `.xlsx` 为后置的excel文件
2. 一个sheet页为一个关键字, sheet页的名称为关键字的名称
3. 第一行传参和返回值, 第二行为对应的值
   1. 传参方式分为三种, 第一种: 无默认值的传参 name, 第二种: 有默认值的传参 name=bob, 第三种: 可变传参 `**kwargs`
   2. 传参的单元格内, 一行表示一个传参, 有几行表示接收几个参数
   3. 返回值必须在下方接口调用时进行定义
4. 第三行接口名称, 参数, 提取, 断言, 从第四行开始后面所有行是对应的数据
   1. 接口名称是在接口文档 `url.xlsx` 中定义的接口名称
   2. 参数是接口请求参数中需要更新的内容, 例如: 接口文档中的请求参数 `{"name": "abc", "age": 21}` 需要将name的值修改, 在关键字中的参数`{"name": "bob"}` 请求时将更新为关键字中的参数
   3. 若有可变传参, 需要将 `**kwargs` 加在参数最后, 例如: `{"name": "abc", "age": 21, **kwargs}`
   4. 提取, 当前仅支持jsonpath的提取
   5. 断言, 当前支持url, body, headers的断言
   
### 编写用例
> 详细使用方式参考后面使用说明
1. 在 `testcase` 文件夹下创建 `.xlsx` 为后置的excel文件
2. sheet页的名称为用例的名称
3. 第一行步骤, 接口, 参数, 提取, 断言, 参数化
   1. 步骤是当前行的步骤名称
   2. 接口, 若是接口文档中的接口, 直接填写接口名称, 若是关键字, 则 `{{关键字名称}}` 这种写法标记是调用关键字
   3. 参数, 正常的json格式数据, 需要进行数据替换, 则 `{{名称}}` 将会被返回值或者参数化中的数据进行替换


## 使用说明

### 返回值
- 会将提取列提取后的值, 赋值给接收的变量

### 接口名称
- `name=创建用户` 说明: 将创建用户接口提取后的返回值, 赋值给name
- `name={{创建用户}}` 说明: 将关键字创建用户的结果返回值, 赋值给name
- `创建用户` 说明: 调用接口创建用户
- `{{创建用户}}` 说明: 调用关键字创建用户

> 特别说明:
> 
>       支持关键字调用关键字
> 
>       关键字中, 名称支持仅使用变量, 例如: info= 此方式可以定义关键字仅仅做数据处理, 不做接口调用, 将数据处理后的结果返回给变量info

### 参数使用
- 在参数列中, 需要进行替换的数据, 使用 `{{名称}}` 的形式进行数据替换, 例如 `{"name": {{name}}}` 将会把变量name的值替换 `{{name}}`
  - **需要注意name的格式问题**
  - 在关键字中, 例如传参定义: `name=abc` , 参数替换后的结果 `{"name": abc}` 不符合json格式, 需要修改传参或者参数定义格式
- 关键字可以使用的参数包含所有的传参和返回值 
- 用例中可以使用的参数包含所有参数化的内容和返回值
- **GET和DELETE的默认传参方式是params, POST和PUT的默认传参方式是json**
- 可以修改默认的传参方式, 使用方式: `data::{"name": {{name}}}` 表示最后使用data的方式传参
- 支持调用python的函数处理数据, 需要在 `data.template.Func` 类下面定义函数名称和执行的内容
  - 使用 `{{Func.demo_func("abc")}}` 来进行使用, Func固定写法, `demo_func` 函数名称, 括号里面为传递的参数
  - 可以使用固定传参 `{{Func.demo_func("abc")}}`
  - 在用例中, 可以使用参数化中的参数的值, 在关键字中, 可以使用关键字传参的值 `{{Func.demo_func(name="{{name}}")}}`, 若要使用此方式, 需要给函数使用装饰器 `render_func`
  - 和python调用函数一样, 需要保证传参正确性

### 关键字调用
- 当关键字的传参中定义**kwargs时, 表示接收可变传参
- 在用例中, 接口名称使用 `{{关键字名称}}` 的形式, 表示调用关键字
- 在参数的单元格内, 一行表示一个传参, 若要传入可变传参必须传入一行json格式的数据
- 不需要关注关键字在哪个excel文件中, 直接通过名称调用即可, 因此需要注意避免关键字重名

### 断言使用
- 可以同时断言多次
- 单元格内, 一行表示一个断言
- 断言格式: `body::{"name": "bob"}` 表示断言响应体的json中, 有 `{"name": "bob"}` 数据
- 断言url: `url::/login` 表示请求的接口url中包含 `/login`
- 断言header: `header::{"content-type": "application/json"}` 表示断言响应头

### 参数化的使用
- 在参数化的单元格内, 一行表示调用一次
- 每行必须是json格式
- 在接口的参数单元格内, 使用 `{{变量名}}` 的形式引用参数化中的变量值
  - 例如: 参数化中: `{"name": "bob"}` , 用例的参数: `{"name": {{name}}, "password": "123456"}`
  - 最后将会把用例中的 `{{name}}` 替换为 `"bob"` 

### 关于网页报告
- 网页报告包含: 环境配置信息, 接口执行情况, 接口耗时统计
- 环境配置信息, config对象的_metadata数据, 可以自行新增
- 接口执行情况, 每个接口的执行情况, 成功或者失败
- 接口耗时, 统计每个调用接口的耗时
- 详细日志结果, 展示执行过程的详细日志信息
- 网页报告会在用例执行完成后, 运行一个本地的http服务, 每次运行前都会检查端口占用并杀死占用进程

### 命令行选项
- `--init` 是否调用初始化函数, 暂无内容
- `--port` 网页报告的监听端口, 默认18050

## 运行
```bash
pip install -r requirements.txt
```
```bash
pytest
```