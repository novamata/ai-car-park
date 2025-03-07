import { createRouter, createWebHistory } from 'vue-router';
import { Auth } from 'aws-amplify';
import LoginCar from '../views/LoginCar.vue';
import RegisterCar from '../views/RegisterCar.vue';
import UserProfileCar from '../views/UserProfileCar.vue';
import HomeCar from '../views/HomeCar.vue';

const routes = [
  {
    path: '/',
    name: 'HomeCar',
    component: HomeCar
  },
  {
    path: '/login',
    name: 'LoginCar',
    component: LoginCar
  },
  {
    path: '/register',
    name: 'RegisterCar',
    component: RegisterCar
  },
  {
    path: '/profile',
    name: 'UserProfileCar',
    component: UserProfileCar,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
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