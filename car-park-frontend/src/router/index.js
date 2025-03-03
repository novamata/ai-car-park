import Vue from 'vue';
import VueRouter from 'vue-router';
import { Auth } from 'aws-amplify';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import UserProfile from '../views/UserProfile.vue';
import Home from '../views/Home.vue';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/profile',
    name: 'Profile',
    component: UserProfile,
    meta: { requiresAuth: true }
  }
];

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
});

router.beforeEach(async (to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    try {
      await Auth.currentAuthenticatedUser();
      next();
    } catch (error) {
      next('/login');
    }
  } else {
    next();
  }
});

export default router;