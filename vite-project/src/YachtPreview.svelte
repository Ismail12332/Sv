<script>
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';
    import { navigate, Link } from 'svelte-navigator';
    import { loadStripe } from '@stripe/stripe-js';
    import Auth0 from 'auth0-js';

    let project = writable(null);
    let vitrine = writable([]);

    let userName = '';
    let userAvatar = '';

    const webAuth = new Auth0.WebAuth({
        domain: 'dev-whbba5qnfveb88fc.us.auth0.com',
        clientID: 'lmZzOfWN5OU25eodYKHpgPaiN67UQ5m3',
        redirectUri: 'https://verboat.com/',
        responseType: 'token id_token',
        scope: 'openid profile email',
        audience: 'http://Survzilla'
    });

    const stripePromise = loadStripe('pk_live_51PMCFt06wu9e4njhVLypDI8aZi9CB653NXS3729hAjXxuzC84b3Y3v7Swd23gGSspSXjqq2Uwrv9FjAPiyV2fDwO00FJq6gYZs');

    const getProjectIdFromPath = () => {
        const pathParts = location.pathname.split('/');
        return pathParts[pathParts.length - 1];
    };

    const project_code = getProjectIdFromPath();

    onMount(async () => {
        saveCurrentPath;
        userName = localStorage.getItem('user_name') || 'User';
        userAvatar = localStorage.getItem('user_avatar');

        const projectResponse = await fetch(`https://verboat.com/api/preview/${project_code}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (projectResponse.ok) {
            const projectData = await projectResponse.json();
            project.set(projectData.project);
        } else if (projectResponse.status === 403) {
            console.error('Access denied. You do not have permission to view this project.');
            navigate('/');  // Redirect to home or any other page
        } else {
            console.error('Failed to fetch project data.');
        }

        const vitrineResponse = await fetch(`https://verboat.com/api/vitrine`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (vitrineResponse.ok) {
            const vitrineData = await vitrineResponse.json();
            vitrine.set(vitrineData.projects);
        } else {
            console.error('Failed to fetch vitrine data.');
        }
    });

    const handleAuthentication = () => {
        webAuth.parseHash((err, authResult) => {
            if (authResult && authResult.accessToken && authResult.idToken) {
                window.location.hash = authResult.state || '';
                localStorage.setItem('accessToken', authResult.accessToken);
                localStorage.setItem('idToken', authResult.idToken);
                console.log('Authentication successful:', authResult);
                const userId = authResult.idTokenPayload.sub; // assuming 'sub' is the user_id
                localStorage.setItem('user_id', userId);
                localStorage.setItem('user_name', authResult.idTokenPayload.name);
                localStorage.setItem('user_avatar', authResult.idTokenPayload.picture);
                navigate(authResult.state || '/');
            } else if (err) {
                console.error(err);
                navigate('/');
            }
        });
    };

    if (window.location.hash.includes('access_token')) {
        handleAuthentication();
    }

    const saveCurrentPath = () => {
        const currentPath = window.location.pathname;
        localStorage.setItem('initialPath', currentPath);
    };

    const viewProject = async (project_id) => {
        const accessToken = localStorage.getItem('accessToken');
        if (!accessToken) {
            saveCurrentPath();
            webAuth.authorize({
                state: window.location.pathname + window.location.search + window.location.hash
            });
            return;
        }

        const response = await fetch(`https://verboat.com/api/check_access/${project_id}`, {
            method: 'GET',
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (data.access) {
                navigate(`/viewproject/${project_id}`);
            } else {
                const stripe = await stripePromise;
                const { error } = await stripe.redirectToCheckout({
                    sessionId: data.sessionId
                });
                if (error) {
                    console.error('Stripe error:', error);
                }
            }
        } else {
            console.error("Failed to check project access.");
            webAuth.authorize({
                state: window.location.pathname + window.location.search + window.location.hash
            });
        }
    };

    const fetchnewproject = async (project_code) => {
        const projectResponse = await fetch(`https://verboat.com/api/preview/${project_code}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (projectResponse.ok) {
            const projectData = await projectResponse.json();
            project.set(projectData.project);
        } else if (projectResponse.status === 403) {
            console.error('Access denied. You do not have permission to view this project.');
            navigate('/');  // Redirect to home or any other page
        } else {
            console.error('Failed to fetch project data.');
        }

        const vitrineResponse = await fetch(`https://verboat.com/api/vitrine`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (vitrineResponse.ok) {
            const vitrineData = await vitrineResponse.json();
            vitrine.set(vitrineData.projects);
        } else {
            console.error('Failed to fetch vitrine data.');
        }
        window.scrollTo(0, 0)
    }

    const login = () => {
        saveCurrentPath();
        webAuth.authorize({
        });
    }
</script>

<style>
    @import '.\public\static\css\index.css';
    @import '.\public\static\css\style.css';
    .project-image {
        width: 100%;
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

<main class="product-detail-page-container">
    <div class="product-detail-page-product-detail-page">
        {#if $project}
        <div class="product-detail-page-copy4">
            <span class="product-detail-page-text34 Heading">
              <span>{$project.vessel_name}</span>
            </span>
            <span class="product-detail-page-text36 Subheading">
              <span>39ft / 2016</span>
            </span>
            <span class="product-detail-page-text38 Subheading">
              <span>${$project.price}</span>
            </span>
            <span class="product-detail-page-text39 Bodytext">
                <span>{$project.description}</span>
              </span>
            <span class="product-detail-page-text40 Bodytext">
              <span>{$project.project_code}</span>
            </span>
            <button class="product-detail-page-button" on:click={viewProject($project.project_id)}>
              <span class="product-detail-page-text42 Smalltext">
                <span>Open Survey</span>
              </span>
            </button>
            <span class="product-detail-page-text44 Smalltext">
              <span>Survey access fee is 10$</span>
            </span>
        </div>
        <div class="product-detail-page-image4">
            <img src={$project.gen_info_image} alt="Vessel Image" class="project-image">
        </div>
        {:else}
            <h1>Hello</h1>
        {/if}

        <span class="product-detail-page-text32 Subheading">
            <span>Similar Category</span>
        </span>
        
        {#if $vitrine.length > 0}
            <div class="product-detail-page-cardlist">
                <div class="product-detail-page-cardgrid">
                    {#each $vitrine as vitrineProject}
                        <div on:click={fetchnewproject(vitrineProject.project_code)}  class="product-detail-page-card">
                            <div class="product-detail-page-image">
                                <img src={vitrineProject.gen_info_image} alt="Vessel Image" class="project-image">
                            </div>
                            <div class="product-detail-page-copy">
                                <span class="product-detail-page-text Bodytext">
                                    <span>{vitrineProject.vessel_name}</span>
                                </span>
                                <span class="product-detail-page-text02 Bodytext">
                                    <span>{vitrineProject.city}</span>
                                    <br />
                                    <span>{vitrineProject.year}</span>
                                </span>
                                <span class="product-detail-page-text06 Bodytext">
                                    <span>${vitrineProject.price}</span>
                                </span>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}

        <div class="product-detail-page-navigation">
            <div class="product-detail-page-items">
                <span class="product-detail-page-text46 Bodytext">
                    <Link to='/'>Home</Link>
                </span>
                <span class="product-detail-page-text48 Bodytext">
                    <Link to='/glav'>Add Survey</Link>
                </span>
                <span class="product-detail-page-text50 Bodytext">
                    <span>Resources</span>
                </span>
                        {#if userAvatar}
                            <span>{userName}</span>
                            <img src={userAvatar} alt="User Avatar" class="user-avatar"/>
                        {:else}
                            <div on:click={login} class="user-avatar-placeholder">Login/Sign Up</div>
                        {/if}
            </div>
            <span class="product-detail-page-text54 Bodytext">
                <h1>VerBoat</h1>
            </span>
            <img
                alt="VerboatLogo02246"
                src="/static/VerboatLogo02.png"
                class="product-detail-page-verboat-logo022"
            />
        </div>
    </div>
</main>

