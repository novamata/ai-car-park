import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import 'bootstrap/dist/css/bootstrap.css';
import BootstrapVue3 from 'bootstrap-vue-3';
import 'bootstrap-vue-3/dist/bootstrap-vue-3.css';

import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.VUE_APP_USER_POOL_ID,
      userPoolClientId: process.env.VUE_APP_USER_POOL_CLIENT_ID,
      region: process.env.VUE_APP_REGION
    }
  },
  API: {
    REST: {
      carParkApi: {
        endpoint: process.env.VUE_APP_API_URL,
        region: process.env.VUE_APP_REGION
      }
    }
  }
});

const app = createApp(App);
app.use(router);
app.use(BootstrapVue3);
app.mount('#app');