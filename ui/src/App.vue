<template>
  <div id="app">
    <h1>Onodanga County E911</h1>
    <select v-model="type">
      <option>pending</option>
      <option>all</option>
      <option>closed</option>
    </select>
    <input v-model="date"></input>
    <button v-on:click="fetchData">Fetch</button>
    <br/><br/>
    <div style='width:100%; margin:0px auto; display:inline-block;'>
    <button v-on:click="prevDay" style="float: left;">←</button>
    <button v-on:click="nextDay" style="float: right;">→</button>
    <br/><br/>
    </div>
    <table>
      <thead>
        <th>#</th>
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
        <td style="white-space:nowrap;">{{ format(row.timestamp, 'h:mm A') }}</td>
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

import ndjsonStream from 'can-ndjson-stream';
import { format, addDays } from 'date-fns';

const fetchNdjson = async function* (url) {
  const response = await fetch(url);
  const exampleStream = ndjsonStream(response.body);
  const reader = exampleStream.getReader();
  let result;
  while (!result || !result.done) {
    result = await reader.read();
    if (result.value) yield result.value;
  }
}

export default {
  name: 'app',
  data () {
    return {
      msg: 'Welcome to Your Vue.js App',
      type: 'all',
      date: format(new Date(), 'YYYY-MM-DD'),
      rows: []
    }
  },
  mounted: async function() {
    await this.fetchData();
  },
  methods: {
    fetchData: async function() {
      this.rows = [];
      const gen = fetchNdjson(`https://s3.amazonaws.com/onondaga-e911-dev/${this.type}/${this.date}.json`);
      const rows = [];
      for await (const row of gen) rows.push(row);
      this.rows = rows;
    },
    nextDay: async function() {
      this.date = format(addDays(this.date, 1), 'YYYY-MM-DD');
      await this.fetchData();
    },
    prevDay: async function() {
      this.date = format(addDays(this.date, -1), 'YYYY-MM-DD');
      await this.fetchData();
    },
    format
  }
}

</script>

<style>

body {
  margin: 0 auto;
  max-width: 85%;
  font-size: 12px;
}

input, select, button, table {
  font-size: 1.2em;
}

/*h1 {
  font-size: 22px;
}*/

#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

h1, h2 {
  font-weight: normal;
  font-size: 3em;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}

table {
  border-collapse: collapse;
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 50px;
}

table, th, td {
  border: 1px solid #eee;
  padding: 0px 10px;
}

</style>
