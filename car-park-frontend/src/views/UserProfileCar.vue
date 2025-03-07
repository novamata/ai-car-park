<template>
  <div class="profile-container">
    <b-card title="Your Profile" class="shadow">
      <b-alert v-if="error" show variant="danger">{{ error }}</b-alert>
      <b-alert v-if="success" show variant="success">{{ success }}</b-alert>
      
      <b-form @submit.prevent="saveProfile">
        <b-form-group label="Name:">
          <b-form-input
            v-model="profile.name"
            required
            placeholder="Enter your name"
          ></b-form-input>
        </b-form-group>
        
        <b-form-group label="Email:">
          <b-form-input
            v-model="profile.email"
            type="email"
            disabled
            placeholder="Your email"
          ></b-form-input>
          <small class="text-muted">Email cannot be changed</small>
        </b-form-group>
        
        <h5 class="mt-4">Your Registration Plates</h5>
        
        <div v-for="(plate, index) in profile.regPlates" :key="index" class="mb-2">
          <b-input-group>
            <b-form-input
              v-model="profile.regPlates[index]"
              placeholder="Registration plate"
            ></b-form-input>
            <b-input-group-append>
              <b-button variant="danger" @click="removePlate(index)">
                <b-icon icon="trash"></b-icon>
              </b-button>
            </b-input-group-append>
          </b-input-group>
        </div>
        
        <b-button variant="outline-primary" @click="addPlate" class="mt-2 mb-4" block>
          <b-icon icon="plus"></b-icon> Add Registration Plate
        </b-button>
        
        <b-button type="submit" variant="primary" :disabled="loading" block>
          {{ loading ? 'Saving...' : 'Save Profile' }}
        </b-button>
      </b-form>
    </b-card>
  </div>
</template>

<script>
import { fetchUserAttributes } from 'aws-amplify/auth';
import { fetchAuthSession } from 'aws-amplify/auth';
import axios from 'axios';

const api = axios.create({
  withCredentials: false, 
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

export default {
  data() {
    return {
      profile: {
        name: '',
        email: '',
        regPlates: []
      },
      loading: false,
      error: null,
      success: null
    };
  },
  async created() {
    await this.loadProfile();
  },
  methods: {
    async loadProfile() {
      this.loading = true;
      this.error = null;
      
      try {
        const attributes = await fetchUserAttributes();
        const { tokens } = await fetchAuthSession();
        const token = tokens.idToken.toString();
        
        this.profile.email = attributes.email;
        
        const response = await api.get(
          `${process.env.VUE_APP_API_URL}/profile`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        
        if (response.data) {
          this.profile.name = response.data.Name || '';
          this.profile.regPlates = response.data.RegPlates || [];
        }
      } catch (error) {
        console.error('Error loading profile:', error);
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          this.error = `Server error: ${error.response.status} - ${error.response.data?.message || 'Unknown error'}`;
        } else if (error.request) {
          // The request was made but no response was received
          this.error = 'No response from server. Please check your connection.';
        } else {
          // Something happened in setting up the request that triggered an Error
          this.error = error.message;
        }
      } finally {
        this.loading = false;
      }
    },
    async saveProfile() {
      this.loading = true;
      this.error = null;
      this.success = null;
      
      try {
        const { tokens } = await fetchAuthSession();
        const token = tokens.idToken.toString();
        
        const payload = {
          name: this.profile.name,
          regPlates: this.profile.regPlates
        };
        
        await api.put(
          `${process.env.VUE_APP_API_URL}/profile`,
          payload,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        
        this.success = 'Profile saved successfully';
      } catch (error) {
        console.error('Error saving profile:', error);
        if (error.response) {
          this.error = `Server error: ${error.response.status} - ${error.response.data?.message || 'Unknown error'}`;
        } else if (error.request) {
          this.error = 'No response from server. Please check your connection.';
        } else {
          this.error = error.message;
        }
      } finally {
        this.loading = false;
      }
    },
    addPlate() {
      this.profile.regPlates.push('');
    },
    removePlate(index) {
      this.profile.regPlates.splice(index, 1);
    }
  }
};
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 50px auto;
}
</style>