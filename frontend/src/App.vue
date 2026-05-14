<template>
  <router-view />
</template>

<script setup>
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif; }

/* 全局表格间隔行颜色（类似 Excel 交替行） */
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: #f0f7ff;
}
.el-table--striped .el-table__body tr.el-table__row--striped:hover td.el-table__cell {
  background: #e0f0ff;
}
.el-table--striped .el-table__body tr:not(.el-table__row--striped):hover td.el-table__cell {
  background: #f5f9ff;
}
</style>
