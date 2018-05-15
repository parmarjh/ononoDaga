<template>
  <div id="home">
    <h1>Onodanga County E911</h1>

    <div class='controls' style='width:100%; margin:0px auto; display:inline-block; text-align: center;'>
      <select v-model="type">
        <option>pending</option>
        <option>all</option>
        <option>closed</option>
      </select>
      <input v-model="date"></input>
      <button v-on:click="fetchData">Fetch</button>

      <button v-on:click="prevDay" style="float: left;">←</button>
      <button v-on:click="nextDay" style="float: right;">→</button>
    <br/><br/>
    </div>

    <DataTable :rows="rows" :noData="noData" :type="currentType" :date="currentDate"></DataTable>

  </div>
</template>

<script>

import ndjsonStream from 'can-ndjson-stream';
import { format, addDays } from 'date-fns';
import DataTable from './DataTable.vue'

const consume = async function (stream) {
  const reader = stream.getReader();
  let result;
  let results = [];
  while (!result || !result.done) {
    result = await reader.read();
    if (result.value) results.push(result.value);
  }
  return results;
}

const fetchNdjson = async function (url) {
  const response = await fetch(url);
  if (response.status === 404) {
    throw new Error("no data")
  }
  const stream = ndjsonStream(response.body);
  return await consume(stream);
}

export default {
  name: 'home',
  props: ['initialType', 'initialDate'],
  data () {
    return {
      type: this.initialType,
      date: this.initialDate,
      rows: [],
      noData: false,
      currentType: '',
      currentDate: '',
    }
  },
  mounted: async function() {
    await this.fetchData();
  },
  methods: {
    fetchData: async function() {
      this.rows = [];
      this.noData = false;
      this.currentType = this.type;
      this.currentDate = this.date;

      this.$router.replace({
        name: 'home',
        path: '*',
        query: { type: this.type, date: this.date }});

      try {
        const rows = await fetchNdjson(`https://s3.amazonaws.com/onondaga-e911-dev/${this.currentType}/${this.currentDate}.json`);
        this.rows = rows;
      } catch(err) {
        this.noData  = true;
      }

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
  },
  components: {
    DataTable
  }
}

</script>

<style>

body {
  margin: 0 auto;
  font-size: 10px;
}

table {
  font-size: 1em;
}

/*h1 {
  font-size: 22px;
}*/

#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  margin: 0 auto;
  max-width: 85%;
}

h1 {
  font-weight: normal;
  font-size: 3em;
}

.controls *, th {
  font-size: 1.2em;
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

</style>
