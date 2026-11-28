import service from './index'

/**
 * 生成本体（上传文档和模拟需求）
 * @param {Object} data - 包含files, simulation_requirement, project_name等
 * @returns {Promise}
 */
export function generateOntology(formData) {
  return service({
    url: '/api/graph/ontology/generate',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 构建图谱
 * @param {Object} data - 包含project_id, graph_name等
 * @returns {Promise}
 */
export function buildGraph(data) {
  return service({
    url: '/api/graph/build',
    method: 'post',
    data
  })
}

/**
 * 查询任务状态
 * @param {String} taskId - 任务ID
 * @returns {Promise}
 */
export function getTaskStatus(taskId) {
  return service({
    url: `/api/graph/task/${taskId}`,
    method: 'get'
  })
}

/**
 * 获取图谱数据
 * @param {String} graphId - 图谱ID
 * @returns {Promise}
 */
export function getGraphData(graphId) {
  return service({
    url: `/api/graph/data/${graphId}`,
    method: 'get'
  })
}

/**
 * 获取项目信息
 * @param {String} projectId - 项目ID
 * @returns {Promise}
 */
export function getProject(projectId) {
  return service({
    url: `/api/graph/project/${projectId}`,
    method: 'get'
  })
}

/**
 * 暂停图谱构建（Zep 批次保留，可续跑）
 * @param {String} projectId
 */
export function pauseGraphBuild(projectId) {
  return service({
    url: `/api/graph/project/${projectId}/pause`,
    method: 'post'
  })
}

/**
 * 继续已暂停的图谱构建（作业已退出时自动重新发起并续跑）
 * @param {String} projectId
 */
export function resumeGraphBuild(projectId) {
  return service({
    url: `/api/graph/project/${projectId}/resume`,
    method: 'post'
  })
}

/**
 * 查询图谱构建作业状态（暂停/运行/完成）
 * @param {String} projectId
 */
export function getGraphBuildJob(projectId) {
  return service({
    url: `/api/graph/project/${projectId}/job`,
    method: 'get'
  })
}
