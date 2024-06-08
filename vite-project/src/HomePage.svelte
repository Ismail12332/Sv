<script>
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';
    import { navigate } from 'svelte-navigator';
    import { loadStripe } from '@stripe/stripe-js';
    import Auth0 from 'auth0-js';
  
    export let webAuth;
  
    let userName = '';
    let userAvatar = '';
    let currentPage = writable(1);
    let projectsPerPage = 12;
    let vitrineProjects = writable([]);
    const stripePromise = loadStripe('pk_live_51PMCFt06wu9e4njhVLypDI8aZi9CB653NXS3729hAjXxuzC84b3Y3v7Swd23gGSspSXjqq2Uwrv9FjAPiyV2fDwO00FJq6gYZs');
    let selectedProject = writable(null);
  
    onMount(async () => {
        userName = localStorage.getItem('user_name') || 'User';
        userAvatar = localStorage.getItem('user_avatar') || 'User image';
  
        const response = await fetch('https://verboat.com/api/vitrine', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
  
        if (response.ok) {
            const data = await response.json();
            vitrineProjects.set(data.projects);
        } else {
            console.error('Failed to fetch vitrine projects.');
        }
    });
  
    const showProject = (project_code) => {
        navigate(`/yachtpreview/${project_code}`);
    };

    const go_in_glav = async () => {
        const accessToken = localStorage.getItem('accessToken');
        if (!accessToken) {
            webAuth.authorize();
            return;
        }
        const response = await fetch('https://verboat.com/cheakglav', {
            method: 'GET',
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`
            }
        });
  
        if (response.ok) {
            const data = await response.json();
            if (data.status === "success") {
                navigate('/glav');
            } else {
                console.error("Failed to fetch project details.");
                webAuth.authorize();
            }
        } else {
            console.error("Failed to fetch project details.");
            webAuth.authorize();
        }
    };
  
    const changePage = (direction) => {
        currentPage.update(n => {
            if (direction === 'next') return n + 1;
            if (direction === 'prev') return n - 1;
            return n;
        });
    };
  
    const login = () => {
        saveCurrentPath();
        webAuth.authorize({
        });
    }
  
    const saveCurrentPath = () => {
        const currentPath = window.location.pathname;
        localStorage.setItem('initialPath', currentPath);
    };

    let boatCode = '';

    const searchBoat = async (event) => {
        event.preventDefault();
        const response = await fetch(`https://verboat.com/api/preview/${boatCode}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.status === 'success') {
                navigate(`/yachtpreview/${boatCode}`);
            } else {
                alert('Sorry, project not found.');
            }
        } else {
            alert('Sorry, project not found.');
        }
    };
  </script>
  
  
  
  <style>
  
  body {
    font-family: "Roboto", sans-serif;
    font-size: 24px;
    color: black;
  }
  
  .container {
    padding: 0 3rem;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2rem;
    background-color: white;
    max-height: 10vh;
  }
  header p {
    font-size: 1.75rem;
    color: black;
    font-weight: 800;
    padding: 2rem 0;
  }
  .logo-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
  }
  
  .logo-container img {
    max-width: 70px;
    height: 70px;
  }
  
  nav ul {
    display: flex;
    gap: 3rem;
    list-style: none;
  }
  
  a {
    text-decoration: none;
    color: black;
  }
  
  .header-right {
    display: flex;
    gap: 3rem;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
  
  button {
    background-color: black;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    border: none;
    cursor: pointer;
    font-size: 1.25rem;
  }
  
  .hero {
    position: relative;
    width: calc(100% + 6rem);
    left: -3rem;
    background-image: url("/static/VerboatBack.png");
    background-size: cover;
    background-position: center;
    height: calc(1024px - 200px);
    background-repeat: no-repeat;
  }
  
  .hero-content {
    margin: 0 auto;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 2rem;
  }
  
  .hero-content h1 {
    font-size: 5rem;
    color: white;
    text-align: center;
    max-width: 30ch;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 1);
    line-height: 1.2;
  }
  
  .hero-content p {
    font-size: 2rem;
    color: white;
    text-align: center;
    max-width: 70ch;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 1);
    line-height: 1.2;
  }
  
  .hero-content form {
    display: flex;
    height: 45px;
    gap: 1rem;
  }
  
  .hero-content input {
    border-radius: 10px;
    padding: 0.5rem 1rem;
    border: none;
    width: 100%;
  }
  .hero-content button {
    background-color: black;
    color: white;
    width: 160px;
    border-radius: 10px;
    cursor: pointer;
    border: none;
  }
  
  .boats-header {
    display: flex;
    justify-content: space-between;
    margin-top: 0;
    margin-bottom: 0;
  }
  .boats-header h2 {
    font-size: 3rem;
    color: black;
    font-weight: 700;
    padding: 2rem 0;
  }
  .boats-header button {
    background-color: white;
    color: black;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    cursor: pointer;
    border: none;
  }
  .card img {
    width: 250px;
    height: 250px;
    border-radius: 10px;
  }
  
  .cards-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 2rem;
  }
  
  .display-boats .more-button {
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    width: 100%;
  }
  .more-button {
    background-color: white;
    color: black;
    padding: 0.5rem 1rem;
    cursor: pointer;
    border: none;
  }
  .card-info h2 {
    font-size: 1.5rem;
    color: black;
    font-weight: 500;
    padding-top: 2rem;
  }
  
  .card-info p {
    font-size: 1.25rem;
    color: black;
    padding: none;
    line-height: 0.75;
  }
  
  .location-year p {
    color: rgb(163, 156, 156);
  }
  .footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1.5px solid rgb(219, 213, 213);
  
    padding: 2rem;
  }
  
  .footer-left {
    display: flex;
    flex-direction: column;
    gap: 6rem;
  }
  .footer-left p {
    font-size: 2rem;
    color: black;
  }
  .footer-links {
    display: flex;
    gap: 2rem;
  }
  
  .footer-links i {
    color: rgb(163, 161, 161);
  }
  
  .footer-right {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    font-size: 1.25rem;
  }
  
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }
  
  /* Remove default margin */
  body,
  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    margin: 0;
  }
  
  html,
  body {
    overflow-x: hidden;
  }
  
  html {
    scroll-behavior: smooth;
  }
  
  /* Set core body defaults */
  body {
    min-height: 100vh;
    font-family: sans-serif;
    font-size: 100%;
    line-height: 1.5;
    text-rendering: optimizeSpeed;
  }
  
  /* Make images easier to work with */
  img {
    display: block;
    max-width: 100%;
  }
  
  /* Inherit fonts for inputs and buttons */
  input,
  button,
  textarea,
  select {
    font: inherit;
  }
  
  /* Remove all animations and transitions for people that prefer not to see them */
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  
    html {
      scroll-behavior: initial;
    }
  }
  
  .pagination {
          display: flex;
          justify-content: center;
          margin-top: 20px;
      }
      .pagination button {
          margin: 0 5px;
          padding: 10px 20px;
          background-color: #444;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
      }
  
      .forprice{
        color: black;
        font-size: 20px;
      }
      .user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: #fff;
      }
      .user-avatar-placeholder {
          gap: 8px;
          display: flex;
          padding: 14px 24px;
          box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.05000000074505806);
          align-items: center;
          border-radius: 8px;
          justify-content: center;
          background-color: rgba(0, 0, 0, 1);
          color: white;
      }
  </style>
  
  <body>
      <div class="container">
        <header>
          <div class="logo-container">
            <img src="/static/VerboatLogo02.png" alt="Logo" />
            <p>VerBoat</p>
          </div>
          <div class="header-right">
            <nav>
              <ul>
                <li><a href="/">Home</a></li>
                <li><a on:click={go_in_glav}>Add Survey</a></li>
              </ul>
            </nav>
            {#if userAvatar}
                  <span>{userName}</span>
                  <img src={userAvatar} alt="User Avatar" class="user-avatar"/>
              {:else}
                  <div on:click={login} class="user-avatar-placeholder">Login/Sign Up</div>
              {/if}
          </div>
        </header>
        <main>
          <section class="hero" >
            <div class="hero-content">
              <h1>VerBoat: Your Trusted Platform for Verified Boat Surveys and Sales</h1>
              <p>
                At Verboat, we understand that buying and selling boats is a significant decision. Our mission is to provide a reliable, transparent,
                and user-friendly platform where boat enthusiasts, owners, and buyers can connect with confidence.
              </p>
            <form on:submit={searchBoat}>
                <input type="text" placeholder="Boat Code" bind:value={boatCode} />
                <button type="submit">Find Boat</button>
            </form>
            </div>
          </section>
          <section>
            <div class="display-boats">
              <div class="boats-header">
                <h2>Boats</h2>
                <button>Filters</button>
              </div>
              <div class="cards-container" id="cards-container">
                {#each $vitrineProjects.slice(($currentPage - 1) * projectsPerPage, $currentPage * projectsPerPage) as project}
                  <div class="card" on:click={() => showProject(project.project_code)}>
                    <img src={project.gen_info_image} alt="Vessel Image">
                    <div class="card-info">
                      <h3>{project.vessel_name}</h3>
                    </div>
                    <div class="location-year">
                      <p>{project.city}</p>
                      <p>{project.year}</p>
                      <p>{project.project_code}</p>
                    </div>
                    <div class="forprice">
                      <p>${project.price}</p>
                    </div>
                  </div>
              {/each}
              </div>
              <div class="pagination">
                <button on:click={() => changePage('prev')}>Previous</button>
                <button on:click={() => changePage('next')}>Next</button>
            </div>
            </div>
          </section>
        </main>
        <footer>
          <div class="footer">
            <div class="footer-left">
              <p>VerBoat 2024</p>
              <div class="footer-links">
                <a href="https://www.facebook.com" target="_blank"><i class="fab fa-facebook-f fa-2x"></i></a>
                <a href="https://www.linkedin.com" target="_blank"><i class="fab fa-linkedin-in fa-2x"></i></a>
                <a href="https://www.youtube.com" target="_blank"><i class="fab fa-youtube fa-2x"></i></a>
                <a href="https://www.instagram.com" target="_blank"><i class="fab fa-instagram fa-2x"></i></a>
              </div>
            </div>
  
            <div class="footer-right">
              <a href="project.html">Project</a>
              <a href="about.html">About</a>
              <a href="contacts.html">Contacts</a>
              <a href="support.html">Support</a>
            </div>
          </div>
        </footer>
      </div>
    </body>

