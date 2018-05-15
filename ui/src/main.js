import 'babel-polyfill';
import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App.vue'
import Home from './Home.vue'

import format from 'date-fns/format';

Vue.use(VueRouter)

const router = new VueRouter({
    mode: 'hash',
    routes: [{
        name: 'home',
        path: '*',
        // Specify the component to be rendered for this route
        component: Home,
        // Inject  props based on route.query values (our query parameters!)
        props: (route) => ({
            initialType: route.query.type || 'all',
            initialDate: route.query.date || format(new Date(), 'YYYY-MM-DD')
        })
    }]
});

new Vue({
  router,
  el: '#app',
  render: h => h(App)
})
