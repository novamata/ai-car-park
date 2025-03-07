import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
// import store from './store';
import 'bootstrap/dist/css/bootstrap.css';
import Amplify from 'aws-amplify';
import BootstrapVue3 from 'bootstrap-vue-3';
import 'bootstrap-vue-3/dist/bootstrap-vue-3.css';

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

const app = createApp(App);
app.use(router);
app.use(BootstrapVue3);
app.mount('#app');