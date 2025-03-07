<template>
  <div class="register-container">
    <b-card title="Register" class="shadow">
      <b-alert v-if="error" show variant="danger">{{ error }}</b-alert>
      <b-alert v-if="success" show variant="success">{{ success }}</b-alert>
      
      <b-form @submit.prevent="register" v-if="!success">
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
          <small class="text-muted">Password must be at least 8 characters with uppercase, lowercase, and numbers</small>
        </b-form-group>
        
        <b-form-group label="Confirm Password:">
          <b-form-input
            v-model="confirmPassword"
            type="password"
            required
            placeholder="Confirm your password"
          ></b-form-input>
        </b-form-group>
        
        <b-button type="submit" variant="primary" :disabled="loading" block>
          {{ loading ? 'Registering...' : 'Register' }}
        </b-button>
      </b-form>
      
      <div v-if="success" class="text-center">
        <p>Please check your email for a verification code.</p>
        <b-form @submit.prevent="confirmSignUp">
          <b-form-group label="Verification Code:">
            <b-form-input
              v-model="code"
              required
              placeholder="Enter verification code"
            ></b-form-input>
          </b-form-group>
          
          <b-button type="submit" variant="primary" :disabled="verifying" block>
            {{ verifying ? 'Verifying...' : 'Verify Account' }}
          </b-button>
        </b-form>
      </div>
      
      <div class="mt-3 text-center">
        <router-link to="/login">Already have an account? Login</router-link>
      </div>
    </b-card>
  </div>
</template>

<script>
import { signUp, confirmSignUp } from 'aws-amplify/auth';

export default {
  data() {
    return {
      email: '',
      password: '',
      confirmPassword: '',
      code: '',
      loading: false,
      verifying: false,
      error: null,
      success: null
    };
  },
  methods: {
    async register() {
      if (this.password !== this.confirmPassword) {
        this.error = 'Passwords do not match';
        return;
      }
      
      this.loading = true;
      this.error = null;
      
      try {
        await signUp({
          username: this.email,
          password: this.password,
          options: {
            userAttributes: {
              email: this.email
            }
          }
        });
        
        this.success = 'Registration successful! Please check your email for verification code.';
      } catch (error) {
        console.error('Error signing up:', error);
        this.error = error.message || 'Failed to register';
      } finally {
        this.loading = false;
      }
    },
    async confirmSignUp() {
      this.verifying = true;
      this.error = null;
      
      try {
        await confirmSignUp({
          username: this.email,
          confirmationCode: this.code
        });
        this.$router.push('/login');
      } catch (error) {
        console.error('Error confirming sign up:', error);
        this.error = error.message || 'Failed to verify account';
      } finally {
        this.verifying = false;
      }
    }
  }
};
</script>

<style scoped>
.register-container {
  max-width: 500px;
  margin: 50px auto;
}
</style>
