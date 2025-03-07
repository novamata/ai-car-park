<template>
  <div class="login-container">
    <b-card title="Login" class="shadow">
      <b-alert v-if="error" show variant="danger">{{ error }}</b-alert>
      
      <b-form @submit.prevent="login">
        <b-form-group label="Email:">
          <b-form-input
            v-model="email"
            type="email"
            required
            placeholder="Enter your email"
          ></b-form-input>
        </b-form-group>
        
        <b-form-group label="Password:">
          <b-form-input
            v-model="password"
            type="password"
            required
            placeholder="Enter your password"
          ></b-form-input>
        </b-form-group>
        
        <b-button type="submit" variant="primary" :disabled="loading" block>
          {{ loading ? 'Logging in...' : 'Login' }}
        </b-button>
      </b-form>
      
      <div class="mt-3 text-center">
        <router-link to="/register">Don't have an account? Register</router-link>
      </div>
    </b-card>
  </div>
</template>

<script>
import { Auth } from 'aws-amplify';

export default {
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      error: null
    };
  },
  methods: {
    async login() {
      this.loading = true;
      this.error = null;
      
      try {
        await Auth.signIn(this.email, this.password);
        this.$router.push('/profile');
      } catch (error) {
        console.error('Error signing in:', error);
        this.error = error.message || 'Failed to login';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.login-container {
  max-width: 500px;
  margin: 50px auto;
}
</style>