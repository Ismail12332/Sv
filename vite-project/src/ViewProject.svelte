<script>
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';
    import { Link } from "svelte-navigator";
    import { navigate } from 'svelte-navigator';

    let project = writable(null);

    const getProjectIdFromPath = () => {
        const pathParts = location.pathname.split('/');
        return pathParts[pathParts.length - 1];
    };

    const project_id = getProjectIdFromPath();

    onMount(() => {
        const fetchProject = async () => {
        if (project_id) {
            const accessToken = localStorage.getItem('accessToken');
            const response = await fetch(`https://verboat.com/api/project/${project_id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            }
            });

            if (response.ok) {
            const data = await response.json();
            project.set(data.project);
            } else if (response.status === 403) {
            console.error('Access denied. You do not have permission to view this project.');
            window.alert('Access denied. You do not have permission to view this project.');
            navigate('/');  // Redirect to home or any other page
            } else {
            console.error('Failed to fetch project data.');
            }
        } else {
            console.error('Project ID is undefined.');
        }
        };

        // Добавляем задержку перед выполнением fetch-запроса
        setTimeout(fetchProject, 3000); // Задержка в 3 секунды
    });



</script>

<style>
    main {
    font-family: 'Roboto', sans-serif;
}
.main-container {
    background-color: #f0f0f0; /* Background color for the margins */
    padding: 20px;
}
.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    background-color: #fff; /* White background for the main content */
    padding: 20px;
}
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    justify-content: space-around;
}
.header img {
    max-height: 100px;
}
.project-info {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 40px;
    flex-direction: column-reverse;
}
.info-text {
    flex: 1;
    margin-left: 20px;
}
.project-image {
    width: 100%;
    height: 550px;
    object-fit: cover;
}
.project-image-glav {
    width: 100%;
    height: 550px;
    object-fit: cover;
    border-radius: 20px;
}
.section {
    margin: 40px 0;
    page-break-inside: avoid; /* Prevents section from breaking */
}
.section-title {
    font-size: 2em;
    text-align: center;
    margin-bottom: 20px;
}
.subsection {
    width: 100%;
    text-align: left;
    margin-bottom: 20px;
    page-break-inside: avoid; /* Prevents subsection from breaking */
}
.subsection-title {
    font-size: 1.5em;
    margin-bottom: 10px;
}
.elements-container {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}
.element {
    box-sizing: border-box;
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    page-break-inside: avoid; /* Prevents element from breaking */
}
.element-title {
    font-size: 1.2em;
    margin-bottom: 10px;
}
.element-content {
    border: 1px solid #ddd;
    padding: 10px;
    border-radius: 5px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    flex-grow: 1;
}
.element img {
    width: 100%;
    height: 200px; /* Fixed height for the images */
    object-fit: cover; /* Maintains aspect ratio while covering the entire area */
}
.element-text {
    margin-top: 10px;
    font-size: 1em;
    flex-grow: 1; /* Allows the text to grow and take up available space */
}
.final-section {
    text-align: center;
    margin-top: 40px;
    padding: 0 100px; /* Added padding for text */
    page-break-inside: avoid; /* Prevents final section from breaking */
}
.final-section h2 {
    font-size: 2em;
    margin-bottom: 20px;
}
.inspection-text {
    font-size: 1em;
    color: #666;
    margin-bottom: 20px;
}
.page-break {
    page-break-before: always; /* Forces page break before this element */
}
</style>

<main>
  <div class="main-container">
    <Link to='/'>Home</Link>
    <div class="container" id="pdfContent">
      <div class="header">
        <h1>VerBoat.com <img src="/static/VerboatLogo02.png" alt="Logo">
            Boat Inspection</h1>
      </div>
      {#if $project}
      <div class="project-info">
        <img src={ $project.main_image } alt="Main Image" class="project-image-glav">
        <div class="info-text">
          <h1>{ $project.boat_make } { $project.boat_model }</h1>
          <p>{ $project.length } ft / { $project.year }</p>
          <p>{ $project.boat_registration }</p>
          <p>Engine: { $project.engine }</p>
          <p>${ $project.price }</p>
          <p>{ $project.city }</p>
          <p>Owner Contact: { $project.owner_contact }</p>
          <p>{ $project.created_at }</p>
        </div>
      </div>
      <div class="project-details">
        {#each Object.keys($project.sections) as sectionKey}
          {#if Object.keys($project.sections[sectionKey]).some(subsectionKey => Object.keys($project.sections[sectionKey][subsectionKey]).some(elementKey => $project.sections[sectionKey][subsectionKey][elementKey].steps?.length > 0 || $project.sections[sectionKey][subsectionKey][elementKey].images?.length > 0))}
            <div class="section">
              <h1 class="section-title">{sectionKey.replace(/_/g, ' ').toUpperCase()}</h1>
              {#each Object.keys($project.sections[sectionKey]) as subsectionKey}
                {#if Object.keys($project.sections[sectionKey][subsectionKey]).some(elementKey => $project.sections[sectionKey][subsectionKey][elementKey].steps?.length > 0 || $project.sections[sectionKey][subsectionKey][elementKey].images?.length > 0)}
                  <div class="subsection">
                    <h2 class="subsection-title">{subsectionKey.replace(/_/g, ' ').toUpperCase()}</h2>
                    <div class="elements-container">
                      {#each Object.keys($project.sections[sectionKey][subsectionKey]) as elementKey}
                        {#if $project.sections[sectionKey][subsectionKey][elementKey].steps?.length > 0 || $project.sections[sectionKey][subsectionKey][elementKey].images?.length > 0}
                          <div class="element">
                            <h3 class="element-title">{elementKey.replace(/_/g, ' ').toUpperCase()}</h3>
                            <div class="element-content">
                              {#if $project.sections[sectionKey][subsectionKey][elementKey].images?.length > 0}
                                {#each $project.sections[sectionKey][subsectionKey][elementKey].images as image}
                                  <img src={image} alt="Element Image" class="project-image" />
                                {/each}
                              {:else}
                                <img src="/static/Noimage.PNG" alt="No Image" class="project-image">
                              {/if}
                              <div class="element-text">
                                {#if $project.sections[sectionKey][subsectionKey][elementKey].text}
                                  <p>{ $project.sections[sectionKey][subsectionKey][elementKey].text }</p>
                                {/if}
                              </div>
                              {#if $project.sections[sectionKey][subsectionKey][elementKey].steps?.length > 0}
                                <ul>
                                  {#each $project.sections[sectionKey][subsectionKey][elementKey].steps as step}
                                    <li>{step}</li>
                                  {/each}
                                </ul>
                              {/if}
                            </div>
                          </div>
                        {/if}
                      {/each}
                    </div>
                  </div>
                {/if}
              {/each}
            </div>
          {/if}
        {/each}
      </div>
      <div class="final-section">
        <h2>Finalizing</h2>
        <p class="inspection-text">This inspection was conducted to the best of my ability, addressing as many issues as possible. I hope it will help you make an informed decision about this boat.</p>
        <p>{ $project.final_note }</p>
        {#if $project.final_kartinka}
          <img src={ $project.final_kartinka } alt="Final Image" class="project-image-glav" />
        {/if}
        <div class="header">
            <h1>VerBoat.com 
                <img src="/static/VerboatLogo02.png" alt="Logo">
            Boat Inspection</h1>
        </div>
      </div>
      {/if}
    </div>
  </div>
</main>


