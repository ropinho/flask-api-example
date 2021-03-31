<template>
  <div id="app">
    <p>{{ greeting }}</p>
    <p>{{ flaskGreeting }}</p>
  </div>
</template>

<script>
export default {
  name: 'App',
  data: function () {
    return {
      greeting: "Hello from Vue",
      flaskGreeting: ""
    }
  },
  created: async function () {
    const gResponse = await fetch("http://localhost:5000/greeting");
    const gObject = await gResponse.json();
    console.log(gObject);
    this.flaskGreeting = gObject.msg;
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
