# 思源API

---

[siyuan/API_zh_CN.md at master · siyuan-note/siyuan](https://github.com/siyuan-note/siyuan/blob/master/API_zh_CN.md)

---

## 规范

### 参数和返回值

- 端点：`http://127.0.0.1:6806`​
- 均是 POST 方法
- 需要带参的接口，参数为 JSON 字符串，放置到 body 里，标头 Content-Type 为 `application/json`​
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {}
  }
  ```

  - `code`​：非 0 为异常情况
  - `msg`​：正常情况下是空字符串，异常情况下会返回错误文案
  - `data`​：可能为 `{}`​、`[]`​ 或者 `NULL`​，根据不同接口而不同

### 鉴权

在 <kbd>设置 - 关于</kbd>​ 里查看 API token，请求标头：`Authorization: Token xxx`​

## 笔记本

### 列出笔记本

- `/api/notebook/lsNotebooks`​
- 不带参
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "notebooks": [
        {
          "id": "20210817205410-2kvfpfn", 
          "name": "测试笔记本",
          "icon": "1f41b",
          "sort": 0,
          "closed": false
        },
        {
          "id": "20210808180117-czj9bvb",
          "name": "思源笔记用户指南",
          "icon": "1f4d4",
          "sort": 1,
          "closed": false
        }
      ]
    }
  }
  ```

### 打开笔记本

- `/api/notebook/openNotebook`​
- 参数

  ```json
  {
    "notebook": "20210831090520-7dvbdv0"
  }
  ```

  - `notebook`​：笔记本 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 关闭笔记本

- `/api/notebook/closeNotebook`​
- 参数

  ```json
  {
    "notebook": "20210831090520-7dvbdv0"
  }
  ```

  - `notebook`​：笔记本 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 重命名笔记本

- `/api/notebook/renameNotebook`​
- 参数

  ```json
  {
    "notebook": "20210831090520-7dvbdv0",
    "name": "笔记本的新名称"
  }
  ```

  - `notebook`​：笔记本 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 创建笔记本

- `/api/notebook/createNotebook`​
- 参数

  ```json
  {
    "name": "笔记本的名称"
  }
  ```
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "notebook": {
        "id": "20220126215949-r1wvoch",
        "name": "笔记本的名称",
        "icon": "",
        "sort": 0,
        "closed": false
      }
    }
  }
  ```

### 删除笔记本

- `/api/notebook/removeNotebook`​
- 参数

  ```json
  {
    "notebook": "20210831090520-7dvbdv0"
  }
  ```

  - `notebook`​：笔记本 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 获取笔记本配置

- `/api/notebook/getNotebookConf`​
- 参数

  ```json
  {
    "notebook": "20210817205410-2kvfpfn"
  }
  ```

  - `notebook`​：笔记本 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "box": "20210817205410-2kvfpfn",
      "conf": {
        "name": "测试笔记本",
        "closed": false,
        "refCreateSavePath": "",
        "createDocNameTemplate": "",
        "dailyNoteSavePath": "/daily note/{{now | date \"2006/01\"}}/{{now | date \"2006-01-02\"}}",
        "dailyNoteTemplatePath": ""
      },
      "name": "测试笔记本"
    }
  }
  ```

### 保存笔记本配置

- `/api/notebook/setNotebookConf`​
- 参数

  ```json
  {
    "notebook": "20210817205410-2kvfpfn",
    "conf": {
        "name": "测试笔记本",
        "closed": false,
        "refCreateSavePath": "",
        "createDocNameTemplate": "",
        "dailyNoteSavePath": "/daily note/{{now | date \"2006/01\"}}/{{now | date \"2006-01-02\"}}",
        "dailyNoteTemplatePath": ""
      }
  }
  ```

  - `notebook`​：笔记本 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "name": "测试笔记本",
      "closed": false,
      "refCreateSavePath": "",
      "createDocNameTemplate": "",
      "dailyNoteSavePath": "/daily note/{{now | date \"2006/01\"}}/{{now | date \"2006-01-02\"}}",
      "dailyNoteTemplatePath": ""
    }
  }
  ```

## 文档

### 列出笔记本下的所有文档

- api/filetree/listDocTree
- 参数

```json
{
    "notebook": "20220407175815-lceq17w",
    "path": "/"
}
```

- 返回值

  ```json
  {
      "code": 0,
      "msg": "",
      "data": {
          "tree": [
              {
                  "id": "20221126104620-m06prws",
                  "children": [
                      {
                          "id": "20230928134805-z11t56h"
                      },
                      {
                          "id": "20231013134532-3426q9j",
                          "children": [
                              {
                                  "id": "20231013134532-60uygtt"
                              },
                              {
                                  "id": "20231013134532-iny1x49"
                              },
                              {
                                  "id": "20231013134532-ng249k4"
                              },
                              {
                                  "id": "20231013134532-o1xpgpz"
                              },
                              {
                                  "id": "20231013134532-u01x7ar",
                                  "children": [
                                      {
                                          "id": "20231013134532-8q4vgf9",
                                          "children": [
                                              {
                                                  "id": "20231013134532-evoj3rm"
                                              }
                                          ]
                                      },
                                      {
                                          "id": "20231013134532-ugrcquk",
                                          "children": [
                                              {
                                                  "id": "20231013134532-yffdan3",
                                                  "children": [
                                                      {
                                                          "id": "20231013134532-9doj565"
                                                      }
                                                  ]
                                              }
                                          ]
                                      }
                                  ]
                              },
                              {
                                  "id": "20231013134532-uiew8a0"
                              }
                          ]
                      },
                      {
                          "id": "20231219230432-4o43kb5",
                          "children": [
                              {
                                  "id": "20240226080709-3wawj1e",
                                  "children": [
                                      {
                                          "id": "20240226083928-ybgmj6j"
                                      }
                                  ]
                              }
                          ]
                      },
                      {
                          "id": "20240107222025-sha60hj",
                          "children": [
                              {
                                  "id": "20240303163613-n04yuyu"
                              },
                              {
                                  "id": "20240303170000-j68d6zp"
                              },
                              {
                                  "id": "20240303170855-kj6t2y2"
                              },
                              {
                                  "id": "20240303170916-cdopw9k"
                              }
                          ]
                      },
                      {
                          "id": "20240109115126-46zrisf"
                      },
                      {
                          "id": "20240118204048-ohgbh7d"
                      },
                      {
                          "id": "20240229223722-jdvoav6"
                      },
                      {
                          "id": "20240301082613-m0l2vcd"
                      },
                      {
                          "id": "20240304105333-v7g5j1s",
                          "children": [
                              {
                                  "id": "20240304105528-2ts7um3"
                              },
                              {
                                  "id": "20240304210415-ykimhdw"
                              }
                          ]
                      },
                      {
                          "id": "20240304115504-1fblbba",
                          "children": [
                              {
                                  "id": "20240116164611-qu06rhl"
                              }
                          ]
                      }
                  ]
              },
              {
                  "id": "20230816232910-dqumxfa",
                  "children": [
                      {
                          "id": "20230908222739-1uk96qm",
                          "children": [
                              {
                                  "id": "20230908213300-r4oa36t"
                              },
                              {
                                  "id": "20230908222815-kr30g7s"
                              },
                              {
                                  "id": "20230909145930-vsl2gs5"
                              }
                          ]
                      },
                      {
                          "id": "20230910090752-1z6h3cj",
                          "children": [
                              {
                                  "id": "20231006095952-o2yl6dh",
                                  "children": [
                                      {
                                          "id": "20231006100024-5rnhpml"
                                      }
                                  ]
                              }
                          ]
                      },
                      {
                          "id": "20230921113853-7llmdlu",
                          "children": [
                              {
                                  "id": "20230914084054-gsgsdqq"
                              },
                              {
                                  "id": "20230922120635-jtitjuz"
                              }
                          ]
                      },
                      {
                          "id": "20231023162743-lci0owb",
                          "children": [
                              {
                                  "id": "20231023162850-l2rt8cg"
                              },
                              {
                                  "id": "20231024085644-iz3xadz"
                              }
                          ]
                      },
                      {
                          "id": "20231025215624-q4joabz",
                          "children": [
                              {
                                  "id": "20231025215634-oe6u7a8",
                                  "children": [
                                      {
                                          "id": "20231025215745-nlfo4ty"
                                      }
                                  ]
                              }
                          ]
                      },
                      {
                          "id": "20231110091057-2yi0aiz",
                          "children": [
                              {
                                  "id": "20231110084756-01unmo5"
                              },
                              {
                                  "id": "20231114213437-c0aqusb"
                              }
                          ]
                      },
                      {
                          "id": "20231208225340-tjwvl36"
                      }
                  ]
              },
              {
                  "id": "20231012194610-v0jqicu"
              },
              {
                  "id": "20231116194604-5rbd1je"
              },
              {
                  "id": "20231225220807-sj8uajj",
                  "children": [
                      {
                          "id": "20240205203349-gwy9vbf"
                      }
                  ]
              },
              {
                  "id": "20231226233056-qfjpl80",
                  "children": [
                      {
                          "id": "20230913101750-lhlgg8u"
                      }
                  ]
              },
              {
                  "id": "20240107180226-s7d75le",
                  "children": [
                      {
                          "id": "20231220201332-xnc07gs"
                      },
                      {
                          "id": "20240107171512-d11936d"
                      }
                  ]
              },
              {
                  "id": "20240114224707-qkvp2y5",
                  "children": [
                      {
                          "id": "20240114224718-2k4ts50"
                      }
                  ]
              },
              {
                  "id": "20240116110639-klk55e2"
              },
              {
                  "id": "20240226092705-i58iqvp",
                  "children": [
                      {
                          "id": "20240304131818-qwy3z9m"
                      }
                  ]
              }
          ]
      }
  }
  ```
  
  



### 通过 Markdown 创建文档

- `/api/filetree/createDocWithMd`​
- 参数

  ```json
  {
    "notebook": "20210817205410-2kvfpfn",
    "path": "/foo/bar",
    "markdown": ""
  }
  ```

  - `notebook`​：笔记本 ID
  - `path`​：文档路径，需要以 / 开头，中间使用 / 分隔层级（这里的 path 对应数据库 hpath 字段）
  - `markdown`​：GFM Markdown 内容
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": "20210914223645-oj2vnx2"
  }
  ```

  - `data`​：创建好的文档 ID
  - 如果使用同一个 `path`​ 重复调用该接口，不会覆盖已有文档

### 重命名文档

- `/api/filetree/renameDoc`​
- 参数

  ```json
  {
    "notebook": "20210831090520-7dvbdv0",
    "path": "/20210902210113-0avi12f.sy",
    "title": "文档新标题"
  }
  ```

  - `notebook`​：笔记本 ID
  - `path`​：文档路径
  - `title`​：新标题
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

通过 `id`​ 重命名文档：

- `/api/filetree/renameDocByID`​
- 参数

  ```json
  {
    "id": "20210902210113-0avi12f",
    "title": "文档新标题"
  }
  ```

  - `id`​：文档 ID
  - `title`​：新标题
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 删除文档

- `/api/filetree/removeDoc`​
- 参数

  ```json
  {
    "notebook": "20210831090520-7dvbdv0",
    "path": "/20210902210113-0avi12f.sy"
  }
  ```

  - `notebook`​：笔记本 ID
  - `path`​：文档路径
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

通过 `id`​ 删除文档：

- `/api/filetree/removeDocByID`​
- 参数

  ```json
  {
    "id": "20210902210113-0avi12f"
  }
  ```

  - `id`​：文档 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 移动文档

- `/api/filetree/moveDocs`​
- 参数

  ```json
  {
    "fromPaths": ["/20210917220056-yxtyl7i.sy"],
    "toNotebook": "20210817205410-2kvfpfn",
    "toPath": "/"
  }
  ```

  - `fromPaths`​：源路径
  - `toNotebook`​：目标笔记本 ID
  - `toPath`​：目标路径
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

通过 `id`​ 移动文档：

- `/api/filetree/moveDocsByID`​
- 参数

  ```json
  {
    "fromIDs": ["20210917220056-yxtyl7i"],
    "toID": "20210817205410-2kvfpfn"
  }
  ```

  - `fromIDs`​：源文档 ID
  - `toID`​：目标父文档 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 根据路径获取人类可读路径

- `/api/filetree/getHPathByPath`​
- 参数

  ```json
  {
    "notebook": "20210831090520-7dvbdv0",
    "path": "/20210917220500-sz588nq/20210917220056-yxtyl7i.sy"
  }
  ```

  - `notebook`​：笔记本 ID
  - `path`​：路径
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": "/foo/bar"
  }
  ```

### 根据 ID 获取人类可读路径

- `/api/filetree/getHPathByID`​
- 参数

  ```json
  {
    "id": "20210917220056-yxtyl7i"
  }
  ```

  - `id`​：块 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": "/foo/bar"
  }
  ```

### 根据 ID 获取存储路径

- `/api/filetree/getPathByID`​
- 参数

  ```json
  {
    "id": "20210808180320-fqgskfj"
  }
  ```

  - `id`​：块 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
    "notebook": "20210808180117-czj9bvb",
    "path": "/20200812220555-lj3enxa/20210808180320-fqgskfj.sy"
    }
  }
  ```

### 根据人类可读路径获取 IDs

- `/api/filetree/getIDsByHPath`​
- 参数

  ```json
  {
    "path": "/foo/bar",
    "notebook": "20210808180117-czj9bvb"
  }
  ```

  - `path`​：人类可读路径
  - `notebook`​：笔记本 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
        "20200813004931-q4cu8na"
    ]
  }
  ```

## 资源文件

### 上传资源文件

- `/api/asset/upload`​
- 参数为 HTTP Multipart 表单

  - `assetsDirPath`​：资源文件存放的文件夹路径，以 data 文件夹作为根路径，比如：

    - `"/assets/"`​：工作空间/data/assets/ 文件夹
    - `"/assets/sub/"`​：工作空间/data/assets/sub/ 文件夹

    常规情况下建议用第一种，统一存放到工作空间资源文件夹下，放在子目录有一些副作用，请参考用户指南资源文件章节。
  - `file[]`​：上传的文件列表
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "errFiles": [""],
      "succMap": {
        "foo.png": "assets/foo-20210719092549-9j5y79r.png"
      }
    }
  }
  ```

  - `errFiles`​：处理时遇到错误的文件名
  - `succMap`​：处理成功的文件，key 为上传时的文件名，value 为 assets/foo-id.png，用于将已有 Markdown 内容中的资源文件链接地址替换为上传后的地址

## 块

### 插入块

- `/api/block/insertBlock`​
- 参数

  ```json
  {
    "dataType": "markdown",
    "data": "foo**bar**{: style=\"color: var(--b3-font-color8);\"}baz",
    "nextID": "",
    "previousID": "20211229114650-vrek5x6",
    "parentID": ""
  }
  ```

  - `dataType`​：待插入数据类型，值可选择 `markdown`​ 或者 `dom`​
  - `data`​：待插入的数据
  - `nextID`​：后一个块的 ID，用于锚定插入位置
  - `previousID`​：前一个块的 ID，用于锚定插入位置
  - `parentID`​：父块 ID，用于锚定插入位置

  `nextID`​、`previousID`​、`parentID`​ 三个参数必须至少存在一个有值，优先级为 `nextID`​ > `previousID`​ > `parentID`​
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      {
        "doOperations": [
          {
            "action": "insert",
            "data": "<div data-node-id=\"20211230115020-g02dfx0\" data-node-index=\"1\" data-type=\"NodeParagraph\" class=\"p\"><div contenteditable=\"true\" spellcheck=\"false\">foo<strong style=\"color: var(--b3-font-color8);\">bar</strong>baz</div><div class=\"protyle-attr\" contenteditable=\"false\"></div></div>",
            "id": "20211230115020-g02dfx0",
            "parentID": "",
            "previousID": "20211229114650-vrek5x6",
            "retData": null
          }
        ],
        "undoOperations": null
      }
    ]
  }
  ```

  - `action.data`​：新插入块生成的 DOM
  - `action.id`​：新插入块的 ID

### 插入前置子块

- `/api/block/prependBlock`​
- 参数

  ```json
  {
    "data": "foo**bar**{: style=\"color: var(--b3-font-color8);\"}baz",
    "dataType": "markdown",
    "parentID": "20220107173950-7f9m1nb"
  }
  ```

  - `dataType`​：待插入数据类型，值可选择 `markdown`​ 或者 `dom`​
  - `data`​：待插入的数据
  - `parentID`​：父块的 ID，用于锚定插入位置
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      {
        "doOperations": [
          {
            "action": "insert",
            "data": "<div data-node-id=\"20220108003710-hm0x9sc\" data-node-index=\"1\" data-type=\"NodeParagraph\" class=\"p\"><div contenteditable=\"true\" spellcheck=\"false\">foo<strong style=\"color: var(--b3-font-color8);\">bar</strong>baz</div><div class=\"protyle-attr\" contenteditable=\"false\"></div></div>",
            "id": "20220108003710-hm0x9sc",
            "parentID": "20220107173950-7f9m1nb",
            "previousID": "",
            "retData": null
          }
        ],
        "undoOperations": null
      }
    ]
  }
  ```

  - `action.data`​：新插入块生成的 DOM
  - `action.id`​：新插入块的 ID

### 插入后置子块

- `/api/block/appendBlock`​
- 参数

  ```json
  {
    "data": "foo**bar**{: style=\"color: var(--b3-font-color8);\"}baz",
    "dataType": "markdown",
    "parentID": "20220107173950-7f9m1nb"
  }
  ```

  - `dataType`​：待插入数据类型，值可选择 `markdown`​ 或者 `dom`​
  - `data`​：待插入的数据
  - `parentID`​：父块的 ID，用于锚定插入位置
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      {
        "doOperations": [
          {
            "action": "insert",
            "data": "<div data-node-id=\"20220108003642-y2wmpcv\" data-node-index=\"1\" data-type=\"NodeParagraph\" class=\"p\"><div contenteditable=\"true\" spellcheck=\"false\">foo<strong style=\"color: var(--b3-font-color8);\">bar</strong>baz</div><div class=\"protyle-attr\" contenteditable=\"false\"></div></div>",
            "id": "20220108003642-y2wmpcv",
            "parentID": "20220107173950-7f9m1nb",
            "previousID": "20220108003615-7rk41t1",
            "retData": null
          }
        ],
        "undoOperations": null
      }
    ]
  }
  ```

  - `action.data`​：新插入块生成的 DOM
  - `action.id`​：新插入块的 ID

### 更新块

- `/api/block/updateBlock`​
- 参数

  ```json
  {
    "dataType": "markdown",
    "data": "foobarbaz",
    "id": "20211230161520-querkps"
  }
  ```

  - `dataType`​：待更新数据类型，值可选择 `markdown`​ 或者 `dom`​
  - `data`​：待更新的数据
  - `id`​：待更新块的 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      {
        "doOperations": [
          {
            "action": "update",
            "data": "<div data-node-id=\"20211230161520-querkps\" data-node-index=\"1\" data-type=\"NodeParagraph\" class=\"p\"><div contenteditable=\"true\" spellcheck=\"false\">foo<strong>bar</strong>baz</div><div class=\"protyle-attr\" contenteditable=\"false\"></div></div>",
            "id": "20211230161520-querkps",
            "parentID": "",
            "previousID": "",
            "retData": null
            }
          ],
        "undoOperations": null
      }
    ]
  }
  ```

  - `action.data`​：更新块生成的 DOM

### 删除块

- `/api/block/deleteBlock`​
- 参数

  ```json
  {
    "id": "20211230161520-querkps"
  }
  ```

  - `id`​：待删除块的 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      {
        "doOperations": [
          {
            "action": "delete",
            "data": null,
            "id": "20211230162439-vtm09qo",
            "parentID": "",
            "previousID": "",
            "retData": null
          }
        ],
       "undoOperations": null
      }
    ]
  }
  ```

### 移动块

- `/api/block/moveBlock`​
- 参数

  ```json
  {
    "id": "20230406180530-3o1rqkc",
    "previousID": "20230406152734-if5kyx6",
    "parentID": "20230404183855-woe52ko"
  }
  ```

  - `id`​：待移动块 ID
  - `previousID`​：前一个块的 ID，用于锚定插入位置
  - `parentID`​：父块的 ID，用于锚定插入位置，`previousID`​ 和 `parentID`​ 不能同时为空，同时存在的话优先使用 `previousID`​
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
        {
            "doOperations": [
                {
                    "action": "move",
                    "data": null,
                    "id": "20230406180530-3o1rqkc",
                    "parentID": "20230404183855-woe52ko",
                    "previousID": "20230406152734-if5kyx6",
                    "nextID": "",
                    "retData": null,
                    "srcIDs": null,
                    "name": "",
                    "type": ""
                }
            ],
            "undoOperations": null
        }
    ]
  }
  ```

### 折叠块

- `/api/block/foldBlock`​
- 参数

  ```json
  {
    "id": "20231224160424-2f5680o"
  }
  ```

  - `id`​：待折叠块的 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 展开块

- `/api/block/unfoldBlock`​
- 参数

  ```json
  {
    "id": "20231224160424-2f5680o"
  }
  ```

  - `id`​：待展开块的 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 获取块 kramdown 源码

- `/api/block/getBlockKramdown`​
- 参数

  ```json
  {
    "id": "20201225220955-l154bn4"
  }
  ```

  - `id`​：待获取块的 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "id": "20201225220955-l154bn4",
      "kramdown": "* {: id=\"20201225220955-2nn1mns\"}新建笔记本，在笔记本下新建文档\n  {: id=\"20210131155408-3t627wc\"}\n* {: id=\"20201225220955-uwhqnug\"}在编辑器中输入 <kbd>/</kbd> 触发功能菜单\n  {: id=\"20210131155408-btnfw88\"}\n* {: id=\"20201225220955-04ymi2j\"}((20200813131152-0wk5akh \"在内容块中遨游\"))、((20200822191536-rm6hwid \"窗口和页签\"))\n  {: id=\"20210131155408-hh1z442\"}"
    }
  }
  ```

### 获取子块

- `/api/block/getChildBlocks`​
- 参数

  ```json
  {
    "id": "20230506212712-vt9ajwj"
  }
  ```

  - `id`​：父块 ID
  - 标题下方块也算作子块
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      {
        "id": "20230512083858-mjdwkbn",
        "type": "h",
        "subType": "h1"
      },
      {
        "id": "20230513213727-thswvfd",
        "type": "s"
      },
      {
        "id": "20230513213633-9lsj4ew",
        "type": "l",
        "subType": "u"
      }
    ]
  }
  ```

### 转移块引用

- `/api/block/transferBlockRef`​
- 参数

  ```json
  {
    "fromID": "20230612160235-mv6rrh1",
    "toID": "20230613093045-uwcomng",
    "refIDs": ["20230613092230-cpyimmd"]
  }
  ```

  - `fromID`​：定义块 ID
  - `toID`​：目标块 ID
  - `refIDs`​：指向定义块 ID 的引用所在块 ID，可选，如果不指定，所有指向定义块 ID 的块引用 ID 都会被转移
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

## 属性

### 设置块属性

- `/api/attr/setBlockAttrs`​
- 参数

  ```json
  {
    "id": "20210912214605-uhi5gco",
    "attrs": {
      "custom-attr1": "line1\nline2"
    }
  }
  ```

  - `id`​：块 ID
  - `attrs`​：块属性，自定义属性必须以 `custom-`​ 作为前缀
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 获取块属性

- `/api/attr/getBlockAttrs`​
- 参数

  ```json
  {
    "id": "20210912214605-uhi5gco"
  }
  ```

  - `id`​：块 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "custom-attr1": "line1\nline2",
      "id": "20210912214605-uhi5gco",
      "title": "PDF 标注双链演示",
      "type": "doc",
      "updated": "20210916120715"
    }
  }
  ```

## SQL

### 执行 SQL 查询

- `/api/query/sql`​
- 参数

  ```json
  {
    "stmt": "SELECT * FROM blocks WHERE content LIKE'%content%' LIMIT 7"
  }
  ```

  - `stmt`​：SQL 脚本
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      { "列": "值" }
    ]
  }
  ```

### 提交事务

- `/api/sqlite/flushTransaction`​
- 不带参
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

## 模板

### 渲染模板

- `/api/template/render`​
- 参数

  ```json
  {
    "id": "20220724223548-j6g0o87",
    "path": "F:\\SiYuan\\data\\templates\\foo.md"
  }
  ```

  - `id`​：调用渲染所在的文档 ID
  - `path`​：模板文件绝对路径
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "content": "<div data-node-id=\"20220729234848-dlgsah7\" data-node-index=\"1\" data-type=\"NodeParagraph\" class=\"p\" updated=\"20220729234840\"><div contenteditable=\"true\" spellcheck=\"false\">foo</div><div class=\"protyle-attr\" contenteditable=\"false\"></div></div>",
      "path": "F:\\SiYuan\\data\\templates\\foo.md"
    }
  }
  ```

### 渲染 Sprig

- `/api/template/renderSprig`​
- 参数

  ```json
  {
    "template": "/daily note/{{now | date \"2006/01\"}}/{{now | date \"2006-01-02\"}}"
  }
  ```

  - `template`​：模板内容
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": "/daily note/2023/03/2023-03-24"
  }
  ```

## 文件

### 获取文件

- `/api/file/getFile`​
- 参数

  ```json
  {
    "path": "/data/20210808180117-6v0mkxr/20200923234011-ieuun1p.sy"
  }
  ```

  - `path`​：工作空间路径下的文件路径
- 返回值

  - 响应状态码 `200`: 文件内容
  - 响应状态码 `202`: 异常信息

    ```json
    {
      "code": 404,
      "msg": "",
      "data": null
    }
    ```

    - `code`: 非零的异常值

      - `-1`: 参数解析错误
      - `403`: 无访问权限 (文件不在工作空间下)
      - `404`: 未找到 (文件不存在)
      - `405`: 方法不被允许 (这是一个目录)
      - `500`: 服务器错误 (文件查询失败 / 文件读取失败)
    - `msg`: 一段描述错误的文本

### 写入文件

- `/api/file/putFile`​
- 参数为 HTTP Multipart 表单

  - `path`​：工作空间路径下的文件路径
  - `isDir`​：是否为创建文件夹，为 `true`​ 时仅创建文件夹，忽略 `file`​
  - `modTime`​：最近访问和修改时间，Unix time
  - `file`​：上传的文件
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 删除文件

- `/api/file/removeFile`​
- 参数

  ```json
  {
    "path": "/data/20210808180117-6v0mkxr/20200923234011-ieuun1p.sy"
  }
  ```

  - `path`​：工作空间路径下的文件路径
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 重命名文件

- `/api/file/renameFile`​
- 参数

  ```json
  {
    "path": "/data/assets/image-20230523085812-k3o9t32.png",
    "newPath": "/data/assets/test-20230523085812-k3o9t32.png"
  }
  ```

  - `path`​：工作空间路径下的文件路径
  - `newPath`​：新的文件路径
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": null
  }
  ```

### 列出文件

- `/api/file/readDir`​
- 参数

  ```json
  {
    "path": "/data/20210808180117-6v0mkxr/20200923234011-ieuun1p"
  }
  ```

  - `path`​：工作空间路径下的文件夹路径
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": [
      {
        "isDir": true,
        "isSymlink": false,
        "name": "20210808180303-6yi0dv5",
        "updated": 1691467624
      },
      {
        "isDir": false,
        "isSymlink": false,
        "name": "20210808180303-6yi0dv5.sy",
        "updated": 1663298365
      }
    ]
  }
  ```

## 导出

### 导出 Markdown 文本

- `/api/export/exportMdContent`​
- 参数

  ```json
  {
    "id": ""
  }
  ```

  - `id`​：要导出的文档块 ID
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "hPath": "/0 请从这里开始",
      "content": "## 🍫 内容块\n\n在思源中，唯一重要的核心概念是..."
    }
  }
  ```

  - `hPath`​：人类可读的路径
  - `content`​：Markdown 内容

### 导出文件与目录

- `/api/export/exportResources`​
- 参数

  ```json
  {
    "paths": [
      "/conf/appearance/boot",
      "/conf/appearance/langs",
      "/conf/appearance/emojis/conf.json",
      "/conf/appearance/icons/index.html"
    ],
    "name": "zip-file-name"
  }
  ```

  - `paths`​：要导出的文件或文件夹路径列表，相同名称的文件/文件夹会被覆盖
  - `name`​：（可选）导出的文件名，未设置时默认为 `export-YYYY-MM-DD_hh-mm-ss.zip`​
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "path": "temp/export/zip-file-name.zip"
    }
  }
  ```

  - `path`​：创建的 `*.zip`​ 文件路径

    - `zip-file-name.zip`​ 中的目录结构如下所示：

      - `zip-file-name`​

        - `boot`​
        - `langs`​
        - `conf.json`​
        - `index.html`​

## 转换

### Pandoc

- `/api/convert/pandoc`​
- 工作目录

  - 执行调用 pandoc 命令时工作目录会被设置在 `工作空间/temp/convert/pandoc/${test}`​ 下
  - 可先通过 API [`写入文件`](#写入文件)​ 将待转换文件写入该目录
  - 然后再调用该 API 进行转换，转换后的文件也会被写入该目录
  - 最后调用 API [`获取文件`](#获取文件)​ 获取转换后的文件内容

    - 或者调用 API [`通过 Markdown 创建文档`](#通过-markdown-创建文档)​
    - 或者调用内部 API `importStdMd`​ 将转换后的文件夹直接导入
- 参数

  ```json
  {
    "dir": "test",
    "args": [
      "--to", "markdown_strict-raw_html",
      "foo.epub",
      "-o", "foo.md"
   ]
  }
  ```

  - `args`​：Pandoc 命令行参数
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
       "path": "/temp/convert/pandoc/test"
    }
  }
  ```

  - `path`​：工作空间下的路径

## 通知

### 推送消息

- `/api/notification/pushMsg`​
- 参数

  ```json
  {
    "msg": "test",
    "timeout": 7000
  }
  ```

  - `timeout`​：消息持续显示时间，单位为毫秒。可以不传入该字段，默认为 7000 毫秒
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
        "id": "62jtmqi"
    }
  }
  ```

  - `id`​：消息 ID

### 推送报错消息

- `/api/notification/pushErrMsg`​
- 参数

  ```json
  {
    "msg": "test",
    "timeout": 7000
  }
  ```

  - `timeout`​：消息持续显示时间，单位为毫秒。可以不传入该字段，默认为 7000 毫秒
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
        "id": "qc9znut"
    }
  }
  ```

  - `id`​：消息 ID

## 网络

### 正向代理

- `/api/network/forwardProxy`​
- 参数

  ```json
  {
    "url": "https://b3log.org/siyuan/",
    "method": "GET",
    "timeout": 7000,
    "contentType": "text/html",
    "headers": [
        {
            "Cookie": ""
        }
    ],
    "payload": {},
    "payloadEncoding": "text",
    "responseEncoding": "text"
  }
  ```

  - `url`​：转发的 URL
  - `method`​：HTTP 方法，默认为 `GET`​
  - `timeout`​：超时时间，单位为毫秒，默认为 `7000`​ 毫秒
  - `contentType`​：HTTP Content-Type，默认为 `application/json`​
  - `headers`​：HTTP 请求标头
  - `payload`​：HTTP 请求体，对象或者是字符串
  - `payloadEncoding`​：`pyaload`​ 所使用的编码方案，默认为 `text`​，可选值如下所示

    - `text`​
    - `base64`​ | `base64-std`​
    - `base64-url`​
    - `base32`​ | `base32-std`​
    - `base32-hex`​
    - `hex`​
  - `responseEncoding`​：响应数据中 `body`​ 字段所使用的编码方案，默认为 `text`​，可选值如下所示

    - `text`​
    - `base64`​ | `base64-std`​
    - `base64-url`​
    - `base32`​ | `base32-std`​
    - `base32-hex`​
    - `hex`​
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "body": "",
      "bodyEncoding": "text",
      "contentType": "text/html",
      "elapsed": 1976,
      "headers": {
      },
      "status": 200,
      "url": "https://b3log.org/siyuan"
    }
  }
  ```

  - `bodyEncoding`​：`body`​ 所使用的编码方案，与请求中 `responseEncoding`​ 字段一致，默认为 `text`​，可能的值如下所示

    - `text`​
    - `base64`​ | `base64-std`​
    - `base64-url`​
    - `base32`​ | `base32-std`​
    - `base32-hex`​
    - `hex`​

## 系统

### 获取启动进度

- `/api/system/bootProgress`​
- 不带参
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": {
      "details": "Finishing boot...",
      "progress": 100
    }
  }
  ```

### 获取系统版本

- `/api/system/version`​
- 不带参
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": "1.3.5"
  }
  ```

### 获取系统当前时间

- `/api/system/currentTime`​
- 不带参
- 返回值

  ```json
  {
    "code": 0,
    "msg": "",
    "data": 1631850968131
  }
  ```
  - `data`: 精度为毫秒
