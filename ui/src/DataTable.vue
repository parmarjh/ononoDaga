<template>

  <div>

    <p class="nodata" v-if="noData">No data found for type: {{type}} | date: {{date}}</p>

    <table v-if="rows.length > 0">
      <thead>
        <th style="width: 20px;">#</th>
        <th>Hash</th>
        <th>Inserted</th>
        <th>Agency</th>
        <th>Time</th>
        <th>Category</th>
        <th>Details</th>
        <th>Address</th>
        <th>Place</th>
        <th>Municipality</th>
        <th>Cross Streets</th>
      </thead>
      <tr v-for="(row, index) in rows" :key="row.timestamp_hash">
        <td>{{ index+1 }}</td>
        <td :title="row.hash">{{ row.hash.slice(0,10) }}</td>
        <td style="white-space:nowrap;">{{ format(row.inserted_timestamp, 'h:mm A') }}</td>
        <td>{{ row.agency }}</td>
        <td style="white-space:nowrap;">{{ row.timestamp ? format(row.timestamp, 'h:mm A') : '' }}</td>
        <td>{{ row.category }}</td>
        <td>{{ row.category_details }}</td>
        <td>{{[row.addr_pre,
               row.addr_name,
               row.addr_type,
               row.addr_suffix].filter(val => val).join(' ')}}</td>
        <td>{{ row.addr_place }}</td>
        <td>{{ row.municipality }}</td>
        <td>{{ row.cross_street1 }} &amp; {{ row.cross_street2 }}</td>
      </tr>
    </table>

  </div>

</template>

<script>

import format from 'date-fns/format';

export default {
  name: 'data-table',
  props: ['rows', 'noData', 'type', 'date'],
  methods: {
    format
  }
}

</script>

<style>

table {
  border-collapse: collapse;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 50px;
  width: 100%;
}

table, th, td {
  border: 1px solid #eee;
  padding: 0px 10px;
}

.nodata {
  font-size: 14px;
}

</style>
