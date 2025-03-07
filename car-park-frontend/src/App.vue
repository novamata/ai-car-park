<template>
  <div id="app">
    <b-navbar toggleable="lg" type="dark" variant="primary">
      <b-navbar-brand to="/">Car Park System</b-navbar-brand>
      
      <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
      
      <b-collapse id="nav-collapse" is-nav>
        <b-navbar-nav>
          <b-nav-item to="/" exact>Home</b-nav-item>
          <b-nav-item to="/profile" v-if="isAuthenticated">My Profile</b-nav-item>
        </b-navbar-nav>
        
        <b-navbar-nav class="ml-auto">
          <template v-if="isAuthenticated">
            <b-nav-item-dropdown right>
              <template #button-content>
                <em>{{ userEmail }}</em>
              </template>
              <b-dropdown-item to="/profile">Profile</b-dropdown-item>
              <b-dropdown-item @click="signOut">Sign Out</b-dropdown-item>
            </b-nav-item-dropdown>
          </template>
          <template v-else>
            <b-nav-item to="/login">Login</b-nav-item>
            <b-nav-item to="/register">Register</b-nav-item>
          </template>
        </b-navbar-nav>
      </b-collapse>
    </b-navbar>
    
    <main class="container mt-4">
      <router-view/>
    </main>
    
    <footer class="bg-light text-center text-muted py-3 mt-5">
      <p class="mb-0">Car Park Management System &copy; {{ new Date().getFullYear() }}</p>
    </footer>
  </div>
</template>

<script>
import { getCurrentUser, signOut } from 'aws-amplify/auth';

export default {
  data() {
    return {
      isAuthenticated: false,
      userEmail: ''
    };
  },
  async created() {
    this.checkAuth();
    setInterval(this.checkAuth, 60000);
  },
  methods: {
    async checkAuth() {
      try {
        const user = await getCurrentUser();
        this.isAuthenticated = true;
        this.userEmail = user.signInDetails?.loginId || '';
      } catch (error) {
        this.isAuthenticated = false;
        this.userEmail = '';
      }
    },
    async signOut() {
      try {
        await signOut();
        this.isAuthenticated = false;
        this.userEmail = '';
        this.$router.push('/login');
      } catch (error) {
        console.error('Error signing out:', error);
      }
    }
  }
};
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}
</style>
