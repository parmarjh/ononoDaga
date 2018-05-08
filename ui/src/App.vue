<template>
  <div id="app">
    <h1>Onodanga County E911</h1>
    <select v-model="type">
      <option>all</option>
      <option>closed</option>
    </select>
    <input v-model="date"></input>
    <button v-on:click="fetchData">Fetch</button>
    <br/><br/>
    <table>
      <thead>
        <th>#</th>
        <th>Agency</th>
        <th>Time</th>
        <th>Category</th>
        <th>Address</th>
        <th>Municipality</th>
        <th>Cross Streets</th>
      </thead>
      <tr v-for="(row, index) in rows" :key="row.timestamp_hash">
        <td>{{ index+1 }}</td>
        <td>{{ row.agency }}</td>
        <td style="white-space:nowrap;">{{ format(row.timestamp, 'h:mm A') }}</td>
        <td>{{ row.category }}</td>
        <td>{{[row.address_pre,
               row.address_name,
               row.address_type,
               row.address_suffix,
               row.address_place].filter(val => val).join(' ')}}</td>
        <td>{{ row.municipality }}</td>
        <td>{{ row.cross_street1 }} &amp; {{ row.cross_street2 }}</td>
      </tr>
    </table>
  </div>
</template>
<script>

import ndjsonStream from 'can-ndjson-stream';
import format from 'date-fns/format';

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
    format
  }
}

</script>

<style>

body {
  margin: 0 auto;
  max-width: 75%;
  font-size: 16px;
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
