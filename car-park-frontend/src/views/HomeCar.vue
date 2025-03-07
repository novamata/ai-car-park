<template>
  <div class="home">
    <div class="jumbotron text-center">
      <h1>Car Park Management System</h1>
      <p class="lead">
        Register your vehicle and receive notifications about your parking sessions
      </p>
      <div v-if="isAuthenticated">
        <b-button variant="primary" to="/profile" class="mr-2">
          My Profile
        </b-button>
        <b-button variant="outline-danger" @click="signOut">
          Sign Out
        </b-button>
      </div>
      <div v-else>
        <b-button variant="primary" to="/login" class="mr-2">
          Login
        </b-button>
        <b-button variant="outline-primary" to="/register">
          Register
        </b-button>
      </div>
    </div>
  </div>
</template>

<script>
import { Auth } from 'aws-amplify';

export default {
  name: 'HomeCar',
  data() {
    return {
      isAuthenticated: false
    };
  },
  async created() {
    try {
      await Auth.currentAuthenticatedUser();
      this.isAuthenticated = true;
    } catch (error) {
      this.isAuthenticated = false;
    }
  },
  methods: {
    async signOut() {
      try {
        await Auth.signOut();
        this.isAuthenticated = false;
        this.$router.push('/login');
      } catch (error) {
        console.error('Error signing out:', error);
      }
    }
  }
};
</script>
