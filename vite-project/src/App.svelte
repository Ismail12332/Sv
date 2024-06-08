<script>
  import { Router, Route, Link } from 'svelte-navigator'
  import { navigate } from 'svelte-navigator'
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import HomePage from './HomePage.svelte';
  import Glav from './Glav.svelte'
  import NotFoundPage from './NotFoundPage.svelte'
  import ViewProject from './ViewProject.svelte';
  import EditProject from "./EditProject.svelte"
  import YachtPreview from './YachtPreview.svelte';
  import Auth0 from 'auth0-js';
  
  const webAuth = new Auth0.WebAuth({
      domain: 'dev-whbba5qnfveb88fc.us.auth0.com',
      clientID: 'lmZzOfWN5OU25eodYKHpgPaiN67UQ5m3',
      redirectUri: 'https://verboat.com/',
      responseType: 'token id_token',
      scope: 'openid profile email',
      audience: 'http://Survzilla'
  });

  onMount(() => {
      // Check for the authentication result
      webAuth.parseHash((err, authResult) => {
      if (authResult && authResult.accessToken && authResult.idToken) {
          localStorage.setItem('accessToken', authResult.accessToken);
          const userId = authResult.idTokenPayload.sub; // assuming 'sub' is the user_id
          localStorage.setItem('user_id', userId);
          localStorage.setItem('user_name', authResult.idTokenPayload.name);
          localStorage.setItem('user_avatar', authResult.idTokenPayload.picture);

          // Retrieve the initial path and navigate to it
          const initialPath = localStorage.getItem('initialPath') || '/';
          navigate(initialPath);
      } else if (err) {
          console.error('Authentication error:', err);
          navigate('/');
      }
      });
  });
</script>



<Router>
  <Route path='/'>
    <HomePage {webAuth}/>
  </Route>

  <Route path='/glav'>
    <Glav {webAuth} />
  </Route>

  <Route path='/EditProject/:project_id'>
    <EditProject {webAuth} />
  </Route>

  <Route path="/yachtpreview/:project_id">
    <YachtPreview />
  </Route>

  <Route path="/viewproject/:project_id">
    <ViewProject />
  </Route>

  <Route path="/*">
    <NotFoundPage />
  </Route>
</Router>

<style>
  
 

  :global(body) {
    margin: 0;
    font-family: 'Open Sans', sans-serif; /* Замените 'Open Sans' на любой шрифт, который вы хотите использовать */
    font-size: 16px;
  }
</style>
