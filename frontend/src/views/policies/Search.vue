<template>
  <div class="policy-search">
    <el-card class="search-card">
      <template #header>
        <div class="card-header">
          <span class="title">政策检索</span>
        </div>
      </template>

      <el-form
        ref="searchFormRef"
        :model="searchForm"
        label-width="100px"
        class="search-form"
      >
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="政策标题">
              <el-input
                v-model="searchForm.title"
                placeholder="请输入政策标题"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="政策分类">
              <el-select
                v-model="searchForm.category"
                placeholder="请选择分类"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="item in categoryOptions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="发布部门">
              <el-input
                v-model="searchForm.department"
                placeholder="请输入发布部门"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="发布时间">
              <el-date-picker
                v-model="searchForm.publishDate"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select
                v-model="searchForm.status"
                placeholder="请选择状态"
                clearable
                style="width: 100%"
              >
                <el-option label="启用" value="active" />
                <el-option label="失效" value="invalid" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="关键词">
              <el-input
                v-model="searchForm.keyword"
                placeholder="请输入关键词"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="result-card">
      <template #header>
        <div class="card-header">
          <span class="title">搜索结果</span>
          <span class="result-count">共 {{ pagination.total }} 条记录</span>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="政策标题" min-width="200">
          <template #default="scope">
            <el-link @click="handleViewDetail(scope.row.id)">{{
              scope.row.title
            }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="categoryName" label="分类" width="120" />
        <el-table-column prop="department" label="发布部门" width="150" />
        <el-table-column prop="publishDate" label="发布日期" width="120" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="scope">
            <el-tag
              :type="scope.row.status === 'active' ? 'success' : 'danger'"
            >
              {{ scope.row.status === "active" ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              link
              @click="handleViewDetail(scope.row.id)"
              >查看详情</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";

import { ref, reactive, onMounted } from "vue";
import { useRouterSafe } from "@/composables/useRouterSafe";
import { ElMessage } from "element-plus";
import request from "@/api/request";

interface Policy {
  id: string;
  title: string;
  category: string;
  categoryName?: string;
  department: string;
  publishDate: string;
  status: "active" | "invalid" | "draft";
  createTime: string;
  updateTime: string;
}

interface Category {
  id: string;
  name: string;
}

const { pushSafe } = useRouterSafe();

const loading = ref(false);
const tableData = ref<Policy[]>([]);
const selectedRows = ref<Policy[]>([]);

const categoryOptions = ref<Category[]>([]);

const searchForm = reactive({
  title: "",
  category: "",
  department: "",
  publishDate: [] as string[],
  status: "",
  keyword: "",
});

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
});

// 加载分类选项
const loadCategories = async () => {
  try {
    const res = await request.get("/policies/categories");
    const data = res.data?.data || res.data;
    // API may return array of categories or a config object
    if (Array.isArray(data)) {
      categoryOptions.value = data as Category[];
    } else {
      // Convert config object to flat category list
      const cats: Category[] = [];
      for (const [key, val] of Object.entries(data || {})) {
        cats.push({ id: key, name: (val as any).label || key });
      }
      categoryOptions.value = cats;
    }
  } catch (error) {
    logger.error("加载政策分类失败:", error);
  }
};

// 加载数据
const loadData = async () => {
  loading.value = true;
  try {
    // Build search keyword: combine title, department, keyword
    const searchParts: string[] = [];
    if (searchForm.title) searchParts.push(searchForm.title);
    if (searchForm.department) searchParts.push(searchForm.department);
    if (searchForm.keyword) searchParts.push(searchForm.keyword);
    const searchStr = searchParts.join(" ") || undefined;

    const res = await request.get("/policies", {
      params: {
        page: pagination.currentPage,
        page_size: pagination.pageSize,
        search: searchStr,
        category: searchForm.category || undefined,
        status: searchForm.status || undefined,
      },
    });
    const data = res.data?.data || res.data;
    const items = data?.items || (Array.isArray(data) ? data : []);

    tableData.value = items.map((item: any) => ({
      id: item.id,
      title: item.title,
      category: item.category,
      categoryName: item.category_name || item.category,
      department: item.department || item.issuing_authority || "",
      publishDate: item.publish_date ? item.publish_date.split("T")[0] : "",
      status: item.status,
      createTime: item.created_at,
      updateTime: item.updated_at,
    }));
    pagination.total = data?.total || items.length;
  } catch (error) {
    logger.error("加载政策数据失败:", error);
    ElMessage.error("加载政策数据失败");
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  pagination.currentPage = 1;
  loadData();
};

// 重置
const handleReset = () => {
  searchForm.title = "";
  searchForm.category = "";
  searchForm.department = "";
  searchForm.publishDate = [];
  searchForm.status = "";
  searchForm.keyword = "";
  pagination.currentPage = 1;
  loadData();
};

// 查看详情
const handleViewDetail = (id: string) => {
  pushSafe(`/policies/${id}`);
};

// 选择变更
const handleSelectionChange = (rows: Policy[]) => {
  selectedRows.value = rows;
};

// 分页大小变更
const handleSizeChange = (val: number) => {
  pagination.pageSize = val;
  pagination.currentPage = 1;
  loadData();
};

// 当前页变更
const handleCurrentChange = (val: number) => {
  pagination.currentPage = val;
  loadData();
};

onMounted(async () => {
  await loadCategories();
  await loadData();
});
</script>

<style scoped>
.policy-search {
  padding: 20px;
  background-color: #0a1929;
  min-height: 100%;
}

.search-card {
  margin-bottom: 20px;
}

.result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #fff;
}

.result-count {
  font-size: 14px;
  color: #ccc;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
