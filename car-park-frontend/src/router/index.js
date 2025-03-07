import { createRouter, createWebHistory } from 'vue-router';
import { getCurrentUser } from 'aws-amplify/auth';
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
      await getCurrentUser();
      next();
    } catch (error) {
      next('/login');
    }
  } else {
    if ((to.name === 'LoginCar' || to.name === 'RegisterCar')) {
      try {
        await getCurrentUser();
        next('/profile');
      } catch {
        next();
      }
    } else {
      next();
    }
  }
});

export default router;