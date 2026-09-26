package co.agrofinca;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class AgrofincaApplication {

    public static void main(String[] args) {
        SpringApplication.run(AgrofincaApplication.class, args);
    }
}
