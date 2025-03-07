import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
// import store from './store';
import 'bootstrap/dist/css/bootstrap.css';
import { Amplify, Auth } from 'aws-amplify';
import BootstrapVue3 from 'bootstrap-vue-3';
import 'bootstrap-vue-3/dist/bootstrap-vue-3.css';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.VUE_APP_USER_POOL_ID,
      userPoolClientId: process.env.VUE_APP_USER_POOL_CLIENT_ID,
      region: process.env.VUE_APP_REGION,
      loginWith: {
        email: true
      }
    }
  },
  API: {
    REST: {
      carParkApi: {
        endpoint: process.env.VUE_APP_API_URL,
        region: process.env.VUE_APP_REGION,
        custom_header: async () => {
          try {
            const session = await Auth.currentSession();
            return {
              Authorization: `Bearer ${session.getIdToken().getJwtToken()}`
            };
          } catch (error) {
            console.error('Error getting auth token:', error);
            return {};
          }
        }
      }
    }
  }
});

const app = createApp(App);
app.use(router);
app.use(BootstrapVue3);
app.mount('#app');