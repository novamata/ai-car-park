import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import { BootstrapVue, IconsPlugin } from 'bootstrap-vue';
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';
import Amplify from 'aws-amplify';

Vue.use(BootstrapVue);
Vue.use(IconsPlugin);

Amplify.configure({
  Auth: {
    region: process.env.VUE_APP_REGION,
    userPoolId: process.env.VUE_APP_USER_POOL_ID,
    userPoolWebClientId: process.env.VUE_APP_USER_POOL_CLIENT_ID,
    mandatorySignIn: true
  },
  API: {
    endpoints: [
      {
        name: 'carParkApi',
        endpoint: process.env.VUE_APP_API_URL,
        custom_header: async () => {
          const session = await Amplify.Auth.currentSession();
          return {
            Authorization: `Bearer ${session.getIdToken().getJwtToken()}`
          };
        }
      }
    ]
  }
});

Vue.config.productionTip = false;

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app');